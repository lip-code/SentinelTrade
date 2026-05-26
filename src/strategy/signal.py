"""Signal definitions for strategy output."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.common.enums import Direction, SignalType
from src.common.types import Signal


class SignalStrength(Enum):
    STRONG = 1.0
    MEDIUM = 0.6
    WEAK = 0.3


@dataclass
class StrategySignal(Signal):
    """Extended signal with strategy-specific fields."""
    ma5: float = 0.0
    ma10: float = 0.0
    ma20: float = 0.0
    trend_score: float = 0.0
