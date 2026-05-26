"""Real QMT broker implementation using xtquant xttrader.

Assembles: QmtClient + OrderManager + TradeCallback + AccountManager
into a production-ready broker for live A-share ETF trading.
"""
from __future__ import annotations

import threading
import time
import uuid
from datetime import datetime

from loguru import logger

from src.broker.account_manager import AccountManager
from src.broker.broker_base import Broker
from src.broker.order_manager import OrderManager
from src.broker.trade_callback import TradeCallback
from src.broker.qmt_client import QmtClient
from src.common.enums import Direction, OrderStatus
from src.common.events import Event, EventBus
from src.common.types import Account, Order, Position, Trade


class _XtCallbackAdapter:
    """Bridges xtquant XtQuantTraderCallback to our TradeCallback."""

    def __init__(self, broker: XtBroker) -> None:
        self._broker = broker

    def on_disconnected(self) -> None:
        logger.warning("QMT trader disconnected")
        self._broker._connected = False

    def on_stock_order(self, order) -> None:
        """Called by xtquant when an order status changes."""
        try:
            xt_order_id = getattr(order, "order_id", 0)
            stock_code = getattr(order, "stock_code", "")
            order_status = getattr(order, "order_status", 0)
            filled_volume = getattr(order, "filled_volume", 0)
            filled_price = getattr(order, "filled_price", 0.0)

            # Find our internal order_id by xt_order_id
            internal_id = None
            for oid, info in self._broker._pending_orders.items():
                if info.get("xt_order_id") == xt_order_id:
                    internal_id = oid
                    break

            if internal_id:
                self._broker._trade_callback.on_order_update(
                    internal_id, order_status, filled_volume, filled_price
                )
                # Remove from pending if terminal state
                if order_status in (1, 3, 4):  # FILLED, CANCELLED, REJECTED
                    self._broker._pending_orders.pop(internal_id, None)
            else:
                logger.warning(f"on_stock_order: unknown xt_order_id={xt_order_id}")
        except Exception as e:
            logger.error(f"on_stock_order error: {e}")

    def on_stock_trade(self, trade) -> None:
        """Called by xtquant when a trade is executed."""
        try:
            stock_code = getattr(trade, "stock_code", "")
            traded_id = getattr(trade, "traded_id", 0)
            traded_volume = getattr(trade, "traded_volume", 0)
            traded_price = getattr(trade, "traded_price", 0.0)

            direction = Direction.BUY if traded_volume > 0 else Direction.SELL
            from src.common.types import Trade as TradeData

            trade_obj = TradeData(
                code=stock_code,
                direction=direction,
                price=traded_price,
                volume=abs(traded_volume),
                commission=0.0,  # xtquant doesn't provide commission in callback
            )
            self._broker._trade_callback.on_trade_report(trade_obj)
        except Exception as e:
            logger.error(f"on_stock_trade error: {e}")

    def on_order_error(self, order_error) -> None:
        """Called by xtquant when an order fails."""
        try:
            xt_order_id = getattr(order_error, "order_id", 0)
            error_msg = getattr(order_error, "error_msg", "unknown")

            internal_id = None
            for oid, info in self._broker._pending_orders.items():
                if info.get("xt_order_id") == xt_order_id:
                    internal_id = oid
                    break

            if internal_id:
                self._broker._trade_callback.on_order_update(internal_id, 4, 0, 0.0)  # REJECTED
                self._broker._pending_orders.pop(internal_id, None)
                logger.error(f"Order error: {internal_id} - {error_msg}")
        except Exception as e:
            logger.error(f"on_order_error error: {e}")


class XtBroker(Broker):
    """Live broker using xtquant xttrader for A-share ETF trading.

    Usage:
        broker = XtBroker(qmt_path, account_id, account_type, event_bus)
        broker.connect()
        order_id = broker.buy("510300", 4.5, 100)
        broker.disconnect()
    """

    def __init__(
        self,
        qmt_path: str,
        account_id: str,
        account_type: str = "STOCK",
        event_bus: EventBus | None = None,
    ) -> None:
        self._qmt_client = QmtClient(qmt_path, account_id, account_type)
        self._order_manager = OrderManager()
        self._account_manager = AccountManager(cache_ttl=3)
        self._event_bus = event_bus or EventBus()
        self._trade_callback = TradeCallback(self._event_bus, self._order_manager)

        self._connected = False
        self._lock = threading.Lock()
        self._pending_orders: dict[str, dict] = {}  # order_id -> xt_order_id mapping

        # xtquant callback adapter (prevent GC)
        self._xt_callback = None

    def connect(self) -> bool:
        """Connect to QMT and register callbacks."""
        success = self._qmt_client.connect()
        if success:
            self._connected = True
            self._register_callbacks()
            self._event_bus.publish(Event(type="broker", data={"status": "connected"}))
        return success

    def disconnect(self) -> None:
        """Disconnect from QMT."""
        self._qmt_client.disconnect()
        self._connected = False
        self._event_bus.publish(Event(type="broker", data={"status": "disconnected"}))

    def is_connected(self) -> bool:
        return self._connected and self._qmt_client.is_connected()

    def reconnect(self, max_retries: int = 5) -> bool:
        """Reconnect with exponential backoff."""
        logger.warning("Attempting reconnect...")
        success = self._qmt_client.reconnect(max_retries)
        if success:
            self._connected = True
            self._register_callbacks()
            self._event_bus.publish(Event(type="broker", data={"status": "reconnected"}))
        return success

    def _register_callbacks(self) -> None:
        """Register xtquant order and trade callbacks."""
        try:
            trader = self._qmt_client.trader
            if trader is None:
                return

            # Create and register callback adapter
            self._xt_callback = _XtCallbackAdapter(self)
            trader.register_callback(self._xt_callback)

            # Subscribe to order/trade updates for this account
            account_id = self._qmt_client.account_id
            account_type = self._qmt_client.account_type
            trader.subscribe_order(account_id, account_type)

            logger.info("xtquant callbacks registered")
        except Exception as e:
            logger.error(f"Failed to register callbacks: {e}")

    def buy(self, code: str, price: float, volume: int) -> str:
        """Submit a buy order.

        Args:
            code: ETF code (e.g., "510300")
            price: Limit price
            volume: Number of shares (must be multiple of 100)

        Returns:
            Internal order_id
        """
        with self._lock:
            if not self.is_connected():
                logger.error("Cannot buy: not connected to QMT")
                return ""

            if volume <= 0 or price <= 0:
                logger.error(f"Invalid order: price={price}, volume={volume}")
                return ""

            # Round volume to 100
            volume = (volume // 100) * 100
            if volume == 0:
                return ""

            try:
                from xtquant import xtconstant
                trader = self._qmt_client.trader
                account_id = self._qmt_client.account_id
                account_type = self._qmt_client.account_type

                xt_order_id = trader.order_stock(
                    account_id=account_id,
                    stock_code=code,
                    order_type=xtconstant.FIX_PRICE,
                    order_volume=volume,
                    price_type=xtconstant.FIX_PRICE,
                    price=price,
                )

                if xt_order_id and xt_order_id > 0:
                    order = self._order_manager.create_order(
                        code=code, direction=Direction.BUY, price=price, volume=volume
                    )
                    self._pending_orders[order.order_id] = {
                        "xt_order_id": xt_order_id,
                        "submitted_at": time.time(),
                    }
                    logger.info(f"BUY submitted: {code} {volume}@{price}, xt_id={xt_order_id}")
                    return order.order_id
                else:
                    logger.error(f"BUY failed: xt_order_id={xt_order_id}")
                    return ""

            except Exception as e:
                logger.error(f"BUY exception: {e}")
                return ""

    def sell(self, code: str, price: float, volume: int) -> str:
        """Submit a sell order.

        Args:
            code: ETF code
            price: Limit price
            volume: Number of shares (must be multiple of 100)

        Returns:
            Internal order_id
        """
        with self._lock:
            if not self.is_connected():
                logger.error("Cannot sell: not connected to QMT")
                return ""

            if volume <= 0 or price <= 0:
                logger.error(f"Invalid order: price={price}, volume={volume}")
                return ""

            volume = (volume // 100) * 100
            if volume == 0:
                return ""

            try:
                from xtquant import xtconstant
                trader = self._qmt_client.trader
                account_id = self._qmt_client.account_id
                account_type = self._qmt_client.account_type

                xt_order_id = trader.order_stock(
                    account_id=account_id,
                    stock_code=code,
                    order_type=xtconstant.FIX_PRICE,
                    order_volume=-volume,  # Negative for sell
                    price_type=xtconstant.FIX_PRICE,
                    price=price,
                )

                if xt_order_id and xt_order_id > 0:
                    order = self._order_manager.create_order(
                        code=code, direction=Direction.SELL, price=price, volume=volume
                    )
                    self._pending_orders[order.order_id] = {
                        "xt_order_id": xt_order_id,
                        "submitted_at": time.time(),
                    }
                    logger.info(f"SELL submitted: {code} {volume}@{price}, xt_id={xt_order_id}")
                    return order.order_id
                else:
                    logger.error(f"SELL failed: xt_order_id={xt_order_id}")
                    return ""

            except Exception as e:
                logger.error(f"SELL exception: {e}")
                return ""

    def cancel_order(self, order_id: str) -> bool:
        """Cancel a pending order."""
        with self._lock:
            if not self.is_connected():
                return False

            pending = self._pending_orders.get(order_id)
            if not pending:
                logger.warning(f"Order {order_id} not found in pending orders")
                return False

            try:
                trader = self._qmt_client.trader
                account_id = self._qmt_client.account_id
                xt_order_id = pending["xt_order_id"]

                trader.cancel_order_stock(account_id, xt_order_id)
                self._order_manager.update_status(order_id, OrderStatus.CANCELLED)
                del self._pending_orders[order_id]
                logger.info(f"Order {order_id} cancelled (xt_id={xt_order_id})")
                return True

            except Exception as e:
                logger.error(f"Cancel order failed: {e}")
                return False

    def get_positions(self) -> list[Position]:
        """Query current positions."""
        if not self.is_connected():
            return []
        return self._account_manager.get_positions(
            self._qmt_client.trader,
            self._qmt_client.account_id,
            self._qmt_client.account_type,
        )

    def get_balance(self) -> Account:
        """Query account balance."""
        if not self.is_connected():
            return Account()
        return self._account_manager.get_balance(
            self._qmt_client.trader,
            self._qmt_client.account_id,
            self._qmt_client.account_type,
        )

    def get_orders(self, status: OrderStatus | None = None) -> list[Order]:
        """Query orders by status."""
        return self._order_manager.get_orders(status)

    def get_trades(self, start: datetime | None = None) -> list[Trade]:
        """Query trade history from filled orders."""
        filled = self._order_manager.get_orders(OrderStatus.FILLED)
        trades = []
        for o in filled:
            if o.filled_volume > 0:
                trades.append(
                    Trade(
                        code=o.code,
                        direction=o.direction,
                        price=o.filled_price,
                        volume=o.filled_volume,
                        commission=0.0,
                    )
                )
        return trades

    def refresh_positions(self) -> list[Position]:
        """Force refresh position cache."""
        self._account_manager.clear_cache()
        return self.get_positions()

    def refresh_balance(self) -> Account:
        """Force refresh balance cache."""
        self._account_manager.clear_cache()
        return self.get_balance()

    @property
    def pending_orders(self) -> dict[str, dict]:
        return dict(self._pending_orders)

    @property
    def qmt_client(self) -> QmtClient:
        return self._qmt_client
