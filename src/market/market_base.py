"""Abstract market data provider interface."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from src.common.types import Bar, Tick


class MarketProvider(ABC):
    @abstractmethod
    def get_realtime_quotes(self, codes: list[str]) -> dict[str, Tick]: ...

    @abstractmethod
    def get_history_bars(self, code: str, period: str, count: int) -> list[Bar]: ...

    @abstractmethod
    def subscribe(self, codes: list[str], callback: Callable[[Tick], None]) -> None: ...

    @abstractmethod
    def connect(self) -> bool: ...

    @abstractmethod
    def disconnect(self) -> None: ...

    @abstractmethod
    def is_connected(self) -> bool: ...
