"""Data access layer for SQLite."""
from __future__ import annotations

from datetime import datetime

from src.common.enums import Direction, SignalType
from src.database.engine import DatabaseEngine


class TradeRepository:
    def __init__(self, engine: DatabaseEngine) -> None:
        self._engine = engine

    def save_trade(
        self,
        code: str,
        direction: Direction,
        price: float,
        volume: int,
        commission: float = 0.0,
        pnl: float = 0.0,
    ) -> int:
        conn = self._engine.connection
        cursor = conn.execute(
            "INSERT INTO trades (code, direction, price, volume, commission, pnl, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (code, direction.value, price, volume, commission, pnl, datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid

    def get_trades(self, limit: int = 100) -> list[dict]:
        cursor = self._engine.connection.execute(
            "SELECT * FROM trades ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]

    def get_daily_pnl(self, date_str: str) -> float:
        cursor = self._engine.connection.execute(
            "SELECT SUM(pnl) as total FROM trades WHERE date(timestamp) = ?", (date_str,)
        )
        row = cursor.fetchone()
        return row["total"] or 0.0


class SignalRepository:
    def __init__(self, engine: DatabaseEngine) -> None:
        self._engine = engine

    def save_signal(
        self,
        code: str,
        signal_type: SignalType,
        strength: float = 0.0,
        price: float = 0.0,
        source: str = "",
    ) -> int:
        conn = self._engine.connection
        cursor = conn.execute(
            "INSERT INTO signals (code, signal_type, strength, price, source, timestamp) VALUES (?, ?, ?, ?, ?, ?)",
            (code, signal_type.value, strength, price, source, datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid

    def get_signals(self, limit: int = 100) -> list[dict]:
        cursor = self._engine.connection.execute(
            "SELECT * FROM signals ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]


class PnlRepository:
    def __init__(self, engine: DatabaseEngine) -> None:
        self._engine = engine

    def save_daily_pnl(self, date_str: str, total_assets: float, pnl: float, drawdown: float) -> int:
        conn = self._engine.connection
        cursor = conn.execute(
            "INSERT OR REPLACE INTO daily_pnl (date, total_assets, pnl, drawdown) VALUES (?, ?, ?, ?)",
            (date_str, total_assets, pnl, drawdown),
        )
        conn.commit()
        return cursor.lastrowid

    def get_pnl_history(self, limit: int = 252) -> list[dict]:
        cursor = self._engine.connection.execute(
            "SELECT * FROM daily_pnl ORDER BY date DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]


class RiskEventRepository:
    def __init__(self, engine: DatabaseEngine) -> None:
        self._engine = engine

    def save_event(self, event_type: str, detail: str = "") -> int:
        conn = self._engine.connection
        cursor = conn.execute(
            "INSERT INTO risk_events (event_type, detail, timestamp) VALUES (?, ?, ?)",
            (event_type, detail, datetime.now().isoformat()),
        )
        conn.commit()
        return cursor.lastrowid

    def get_events(self, limit: int = 100) -> list[dict]:
        cursor = self._engine.connection.execute(
            "SELECT * FROM risk_events ORDER BY timestamp DESC LIMIT ?", (limit,)
        )
        return [dict(row) for row in cursor.fetchall()]
