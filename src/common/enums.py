from enum import Enum, auto


class Direction(Enum):
    BUY = "buy"
    SELL = "sell"


class OrderStatus(Enum):
    PENDING = "pending"
    FILLED = "filled"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class SignalType(Enum):
    ENTRY = "entry"
    EXIT = "exit"
    STOP_LOSS = "stop_loss"
    STOP_PROFIT = "stop_profit"


class TrendDirection(Enum):
    UP = "up"
    DOWN = "down"
    SIDEWAYS = "sideways"
