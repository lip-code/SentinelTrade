"""Trade callback handler for xtquant events."""
from __future__ import annotations

from loguru import logger

from src.common.enums import Direction, OrderStatus
from src.common.events import Event, EventBus
from src.common.types import Trade
from src.broker.order_manager import OrderManager


class TradeCallback:
    """Handles order and trade callbacks from xtquant."""

    def __init__(self, event_bus: EventBus, order_manager: OrderManager) -> None:
        self._event_bus = event_bus
        self._order_manager = order_manager

    def on_order_update(self, order_id: str, status: int, filled_volume: int, filled_price: float) -> None:
        try:
            status_map = {
                0: OrderStatus.PENDING,
                1: OrderStatus.FILLED,
                2: OrderStatus.PARTIAL,
                3: OrderStatus.CANCELLED,
                4: OrderStatus.REJECTED,
            }
            order_status = status_map.get(status, OrderStatus.PENDING)
            self._order_manager.update_status(order_id, order_status, filled_volume, filled_price)
            logger.info(f"Order {order_id} status: {order_status.value}")
        except Exception as e:
            logger.error(f"on_order_update error: {e}")

    def on_trade_report(self, trade: Trade) -> None:
        try:
            self._event_bus.publish(Event(type="trade", data={"trade": trade}))
            logger.info(
                f"Trade: {trade.code} {trade.direction.value} {trade.volume}@{trade.price}"
            )
        except Exception as e:
            logger.error(f"on_trade_report error: {e}")
