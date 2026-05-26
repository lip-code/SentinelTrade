"""Market data cache with TTL expiration."""
from __future__ import annotations

import time

from src.common.types import Tick


class DataCache:
    def __init__(self, ttl_seconds: int = 60) -> None:
        self._ttl = ttl_seconds
        self._ticks: dict[str, tuple[Tick, float]] = {}
        self._bars: dict[str, tuple[list, float]] = {}

    def get_tick(self, code: str) -> Tick | None:
        entry = self._ticks.get(code)
        if entry is None:
            return None
        tick, ts = entry
        if time.time() - ts > self._ttl:
            del self._ticks[code]
            return None
        return tick

    def set_tick(self, code: str, tick: Tick) -> None:
        self._ticks[code] = (tick, time.time())

    def get_bars(self, key: str) -> list | None:
        entry = self._bars.get(key)
        if entry is None:
            return None
        bars, ts = entry
        if time.time() - ts > self._ttl:
            del self._bars[key]
            return None
        return bars

    def set_bars(self, key: str, bars: list) -> None:
        self._bars[key] = (bars, time.time())

    def clear(self) -> None:
        self._ticks.clear()
        self._bars.clear()
