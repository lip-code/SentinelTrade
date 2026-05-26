"""Abstract broker interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime

from src.common.enums import OrderStatus
from src.common.types import Account, Order, Position, Trade


class Broker(ABC):
    @abstractmethod
    def buy(self, code: str, price: float, volume: int) -> str: ...

    @abstractmethod
    def sell(self, code: str, price: float, volume: int) -> str: ...

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool: ...

    @abstractmethod
    def get_positions(self) -> list[Position]: ...

    @abstractmethod
    def get_balance(self) -> Account: ...

    @abstractmethod
    def get_orders(self, status: OrderStatus | None = None) -> list[Order]: ...

    @abstractmethod
    def get_trades(self, start: datetime | None = None) -> list[Trade]: ...
