"""Abstract strategy interface."""
from __future__ import annotations

from abc import ABC, abstractmethod

from src.common.types import Bar, Signal


class Strategy(ABC):
    @abstractmethod
    def on_bar(self, bars: dict[str, Bar]) -> list[Signal]: ...

    @abstractmethod
    def get_params(self) -> dict: ...

    @abstractmethod
    def update_params(self, params: dict) -> None: ...
