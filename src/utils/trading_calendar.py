"""A-share trading calendar utility."""
from __future__ import annotations

from datetime import date, timedelta


class TradingCalendar:
    """A-share trading calendar. Handles weekends and configurable holidays."""

    def __init__(self, holidays: list[date] | None = None) -> None:
        self._holidays: set[date] = set(holidays or [])

    def is_trading_day(self, d: date) -> bool:
        if d.weekday() >= 5:
            return False
        return d not in self._holidays

    def next_trading_day(self, d: date) -> date:
        next_day = d + timedelta(days=1)
        while not self.is_trading_day(next_day):
            next_day += timedelta(days=1)
        return next_day

    def prev_trading_day(self, d: date) -> date:
        prev_day = d - timedelta(days=1)
        while not self.is_trading_day(prev_day):
            prev_day -= timedelta(days=1)
        return prev_day

    def trading_days_between(self, start: date, end: date) -> list[date]:
        days = []
        current = start
        while current <= end:
            if self.is_trading_day(current):
                days.append(current)
            current += timedelta(days=1)
        return days
