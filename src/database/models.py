"""Database table model definitions (schema reference)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass
class TradeRecord:
    id: int = 0
    code: str = ""
    direction: str = ""
    price: float = 0.0
    volume: int = 0
    commission: float = 0.0
    pnl: float = 0.0
    timestamp: str = ""


@dataclass
class SignalRecord:
    id: int = 0
    code: str = ""
    signal_type: str = ""
    strength: float = 0.0
    price: float = 0.0
    source: str = ""
    timestamp: str = ""


@dataclass
class DailyPnlRecord:
    id: int = 0
    date: str = ""
    total_assets: float = 0.0
    pnl: float = 0.0
    drawdown: float = 0.0


@dataclass
class RiskEventRecord:
    id: int = 0
    event_type: str = ""
    detail: str = ""
    timestamp: str = ""
