"""Order management with duplicate prevention."""
from __future__ import annotations

import uuid

from loguru import logger

from src.common.enums import Direction, OrderStatus
from src.common.types import Order


class OrderManager:
    """Manages order lifecycle and prevents duplicate orders."""

    def __init__(self) -> None:
        self._orders: dict[str, Order] = {}
        self._pending_codes: set[str] = set()

    def create_order(self, code: str, direction: Direction, price: float, volume: int) -> Order:
        order_id = uuid.uuid4().hex[:12]
        order = Order(
            order_id=order_id,
            code=code,
            direction=direction,
            price=price,
            volume=volume,
            status=OrderStatus.PENDING,
        )
        self._orders[order_id] = order
        return order

    def is_duplicate(self, code: str, direction: Direction) -> bool:
        key = f"{code}_{direction.value}"
        if key in self._pending_codes:
            return True
        self._pending_codes.add(key)
        return False

    def clear_pending(self, code: str, direction: Direction) -> None:
        key = f"{code}_{direction.value}"
        self._pending_codes.discard(key)

    def update_status(
        self,
        order_id: str,
        status: OrderStatus,
        filled_volume: int = 0,
        filled_price: float = 0.0,
    ) -> None:
        order = self._orders.get(order_id)
        if order:
            order.status = status
            order.filled_volume = filled_volume
            order.filled_price = filled_price
            if status in (OrderStatus.FILLED, OrderStatus.CANCELLED, OrderStatus.REJECTED):
                self.clear_pending(order.code, order.direction)

    def get_order(self, order_id: str) -> Order | None:
        return self._orders.get(order_id)

    def get_orders(self, status: OrderStatus | None = None) -> list[Order]:
        if status is None:
            return list(self._orders.values())
        return [o for o in self._orders.values() if o.status == status]
