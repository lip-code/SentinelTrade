"""Account and position query with caching."""
from __future__ import annotations

import time

from loguru import logger

from src.common.types import Account, Position


class AccountManager:
    """Queries positions and balance from xttrader with TTL cache."""

    def __init__(self, cache_ttl: int = 5) -> None:
        self._cache_ttl = cache_ttl
        self._positions_cache: tuple[list[Position], float] | None = None
        self._balance_cache: tuple[Account, float] | None = None

    def get_positions(self, trader, account_id: str, account_type: str) -> list[Position]:
        if self._positions_cache:
            positions, ts = self._positions_cache
            if time.time() - ts < self._cache_ttl:
                return positions
        try:
            positions = []
            if trader:
                raw = trader.query_stock_positions(account_id, account_type)
                for item in raw:
                    positions.append(Position(
                        code=item.stock_code,
                        volume=item.volume,
                        available=item.can_use_volume,
                        cost_price=item.open_price,
                        current_price=item.market_value / item.volume if item.volume > 0 else 0,
                        market_value=item.market_value,
                    ))
            self._positions_cache = (positions, time.time())
            return positions
        except Exception as e:
            logger.error(f"get_positions error: {e}")
            return self._positions_cache[0] if self._positions_cache else []

    def get_balance(self, trader, account_id: str, account_type: str) -> Account:
        if self._balance_cache:
            account, ts = self._balance_cache
            if time.time() - ts < self._cache_ttl:
                return account
        try:
            if trader:
                raw = trader.query_stock_asset(account_id, account_type)
                account = Account(
                    total_assets=raw.total_asset,
                    balance=raw.cash,
                    available=raw.cash - raw.frozen_cash,
                    frozen=raw.frozen_cash,
                    market_value=raw.market_value,
                )
            else:
                account = Account()
            self._balance_cache = (account, time.time())
            return account
        except Exception as e:
            logger.error(f"get_balance error: {e}")
            return self._balance_cache[0] if self._balance_cache else Account()

    def clear_cache(self) -> None:
        self._positions_cache = None
        self._balance_cache = None
