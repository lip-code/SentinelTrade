"""Risk rule abstract base class and context/result types."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime

from src.common.types import Account, Position, Signal, Trade


@dataclass
class RiskContext:
    """Context passed to risk rules for evaluation."""
    positions: list[Position] = field(default_factory=list)
    account: Account = field(default_factory=Account)
    daily_trades: list[Trade] = field(default_factory=list)
    current_time: datetime = field(default_factory=datetime.now)
    is_connected: bool = True
    has_market_data: bool = True


@dataclass
class RiskResult:
    """Result of a risk rule check."""
    passed: bool = True
    reason: str = ""
    rule_name: str = ""


class RiskRule(ABC):
    """Abstract risk rule. Each rule checks one specific risk dimension."""

    @abstractmethod
    def check(self, signal: Signal, context: RiskContext) -> RiskResult: ...

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def priority(self) -> int: ...
