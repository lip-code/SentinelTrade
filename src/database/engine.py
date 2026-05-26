"""SQLite database connection manager."""
from __future__ import annotations

import sqlite3
from pathlib import Path


class DatabaseEngine:
    """Singleton-like SQLite connection manager."""

    def __init__(self, db_path: str = "data/sentinel.db") -> None:
        self._db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row

    @property
    def connection(self) -> sqlite3.Connection:
        return self._conn

    def init_tables(self) -> None:
        cursor = self._conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                direction TEXT NOT NULL,
                price REAL NOT NULL,
                volume INTEGER NOT NULL,
                commission REAL DEFAULT 0,
                pnl REAL DEFAULT 0,
                timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS signals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL,
                signal_type TEXT NOT NULL,
                strength REAL DEFAULT 0,
                price REAL DEFAULT 0,
                source TEXT DEFAULT '',
                timestamp TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS daily_pnl (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL UNIQUE,
                total_assets REAL NOT NULL,
                pnl REAL DEFAULT 0,
                drawdown REAL DEFAULT 0
            );
            CREATE TABLE IF NOT EXISTS risk_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                detail TEXT DEFAULT '',
                timestamp TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()
