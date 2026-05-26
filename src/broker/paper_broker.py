"""Paper trading broker for backtesting and testing."""
from __future__ import annotations

import uuid
from datetime import datetime

from loguru import logger

from src.broker.broker_base import Broker
from src.common.enums import Direction, OrderStatus
from src.common.types import Account, Order, Position, Trade


class PaperBroker(Broker):
    """Simulated broker with in-memory matching engine."""

    def __init__(self, initial_balance: float = 30000.0, commission_rate: float = 0.0003) -> None:
        self._balance = initial_balance
        self._initial_balance = initial_balance
        self._commission_rate = commission_rate
        self._positions: dict[str, Position] = {}
        self._orders: list[Order] = []
        self._trades: list[Trade] = []

    def buy(self, code: str, price: float, volume: int) -> str:
        cost = price * volume
        commission = max(cost * self._commission_rate, 5.0)
        total_cost = cost + commission

        if total_cost > self._balance:
            order = Order(
                order_id=uuid.uuid4().hex[:12],
                code=code,
                direction=Direction.BUY,
                price=price,
                volume=volume,
                status=OrderStatus.REJECTED,
            )
            self._orders.append(order)
            logger.warning(f"Paper BUY rejected: insufficient balance for {code}")
            return order.order_id

        self._balance -= total_cost

        if code in self._positions:
            pos = self._positions[code]
            total_volume = pos.volume + volume
            pos.cost_price = (pos.cost_price * pos.volume + price * volume) / total_volume
            pos.volume = total_volume
            pos.available = total_volume
        else:
            self._positions[code] = Position(
                code=code,
                volume=volume,
                available=volume,
                cost_price=price,
                current_price=price,
                market_value=price * volume,
            )

        order = Order(
            order_id=uuid.uuid4().hex[:12],
            code=code,
            direction=Direction.BUY,
            price=price,
            volume=volume,
            status=OrderStatus.FILLED,
            filled_volume=volume,
            filled_price=price,
        )
        self._orders.append(order)

        trade = Trade(
            trade_id=uuid.uuid4().hex[:12],
            order_id=order.order_id,
            code=code,
            direction=Direction.BUY,
            price=price,
            volume=volume,
            commission=commission,
        )
        self._trades.append(trade)

        logger.info(f"Paper BUY: {code} {volume}@{price}, commission={commission:.2f}")
        return order.order_id

    def sell(self, code: str, price: float, volume: int) -> str:
        pos = self._positions.get(code)
        if not pos or pos.available < volume:
            order = Order(
                order_id=uuid.uuid4().hex[:12],
                code=code,
                direction=Direction.SELL,
                price=price,
                volume=volume,
                status=OrderStatus.REJECTED,
            )
            self._orders.append(order)
            return order.order_id

        revenue = price * volume
        commission = max(revenue * self._commission_rate, 5.0)
        self._balance += revenue - commission

        pos.volume -= volume
        pos.available -= volume
        pos.market_value = pos.current_price * pos.volume
        if pos.volume == 0:
            del self._positions[code]

        order = Order(
            order_id=uuid.uuid4().hex[:12],
            code=code,
            direction=Direction.SELL,
            price=price,
            volume=volume,
            status=OrderStatus.FILLED,
            filled_volume=volume,
            filled_price=price,
        )
        self._orders.append(order)

        pnl = (price - pos.cost_price) * volume - commission
        trade = Trade(
            trade_id=uuid.uuid4().hex[:12],
            order_id=order.order_id,
            code=code,
            direction=Direction.SELL,
            price=price,
            volume=volume,
            commission=commission,
        )
        self._trades.append(trade)

        logger.info(f"Paper SELL: {code} {volume}@{price}, pnl={pnl:.2f}")
        return order.order_id

    def cancel_order(self, order_id: str) -> bool:
        return False

    def get_positions(self) -> list[Position]:
        return list(self._positions.values())

    def get_balance(self) -> Account:
        market_value = sum(p.market_value for p in self._positions.values())
        return Account(
            total_assets=self._balance + market_value,
            balance=self._balance,
            available=self._balance,
            frozen=0.0,
            market_value=market_value,
        )

    def get_orders(self, status: OrderStatus | None = None) -> list[Order]:
        if status is None:
            return self._orders
        return [o for o in self._orders if o.status == status]

    def get_trades(self, start: datetime | None = None) -> list[Trade]:
        if start is None:
            return self._trades
        return [t for t in self._trades if t.timestamp >= start]
