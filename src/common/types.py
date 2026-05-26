from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from src.common.enums import Direction, OrderStatus, SignalType


@dataclass
class Bar:
    code: str = ""
    open: float = 0.0
    high: float = 0.0
    low: float = 0.0
    close: float = 0.0
    volume: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Tick:
    code: str = ""
    last_price: float = 0.0
    bid_price: float = 0.0
    ask_price: float = 0.0
    volume: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Signal:
    code: str = ""
    direction: Direction = Direction.BUY
    signal_type: SignalType = SignalType.ENTRY
    strength: float = 0.0
    price: float = 0.0
    source: str = ""
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Order:
    order_id: str = ""
    code: str = ""
    direction: Direction = Direction.BUY
    price: float = 0.0
    volume: int = 0
    status: OrderStatus = OrderStatus.PENDING
    filled_volume: int = 0
    filled_price: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Trade:
    trade_id: str = ""
    order_id: str = ""
    code: str = ""
    direction: Direction = Direction.BUY
    price: float = 0.0
    volume: int = 0
    commission: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Position:
    code: str = ""
    name: str = ""
    volume: int = 0
    available: int = 0
    cost_price: float = 0.0
    current_price: float = 0.0
    market_value: float = 0.0
    pnl: float = 0.0
    pnl_ratio: float = 0.0


@dataclass
class Account:
    total_assets: float = 0.0
    balance: float = 0.0
    available: float = 0.0
    frozen: float = 0.0
    market_value: float = 0.0
    daily_pnl: float = 0.0
