"""xtquant market data provider implementation."""
from __future__ import annotations

from typing import Callable

import pandas as pd
from loguru import logger

from src.common.types import Bar, Tick
from src.market.data_cache import DataCache
from src.market.market_base import MarketProvider


class XtProvider(MarketProvider):
    """Market data provider using xtquant xtdata."""

    def __init__(self, qmt_path: str = "") -> None:
        self._qmt_path = qmt_path
        self._connected = False
        self._cache = DataCache(ttl_seconds=30)

    def connect(self) -> bool:
        try:
            from xtquant import xtdata
            xtdata.connect()
            self._connected = True
            logger.info("xtdata connected")
            return True
        except Exception as e:
            logger.error(f"xtdata connect failed: {e}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        self._connected = False

    def is_connected(self) -> bool:
        return self._connected

    def get_realtime_quotes(self, codes: list[str]) -> dict[str, Tick]:
        result: dict[str, Tick] = {}
        try:
            from xtquant import xtdata
            xtdata.subscribe_quote(codes, period="tick", count=-1)
            raw = xtdata.get_full_tick(codes)
            for code, data in raw.items():
                tick = Tick(
                    code=code,
                    last_price=data.get("lastPrice", 0.0),
                    bid_price=data.get("bidPrice", [0.0])[0] if data.get("bidPrice") else 0.0,
                    ask_price=data.get("askPrice", [0.0])[0] if data.get("askPrice") else 0.0,
                    volume=data.get("volume", 0),
                )
                self._cache.set_tick(code, tick)
                result[code] = tick
        except Exception as e:
            logger.error(f"get_realtime_quotes failed: {e}")
            for code in codes:
                cached = self._cache.get_tick(code)
                if cached:
                    result[code] = cached
        return result

    def get_history_bars(self, code: str, period: str, count: int) -> list[Bar]:
        cache_key = f"{code}_{period}_{count}"
        cached = self._cache.get_bars(cache_key)
        if cached:
            return cached

        try:
            from xtquant import xtdata
            xtdata.subscribe_quote(code, period=period, count=count)
            data = xtdata.get_market_data_ex(
                field_list=[], stock_list=[code], period=period, count=count
            )
            bars: list[Bar] = []
            if code in data:
                df = data[code]
                for _, row in df.iterrows():
                    bars.append(Bar(
                        code=code,
                        open=row["open"],
                        high=row["high"],
                        low=row["low"],
                        close=row["close"],
                        volume=row["volume"],
                    ))
            self._cache.set_bars(cache_key, bars)
            return bars
        except Exception as e:
            logger.error(f"get_history_bars failed for {code}: {e}")
            return []

    def subscribe(self, codes: list[str], callback: Callable[[Tick], None]) -> None:
        try:
            from xtquant import xtdata
            for code in codes:
                xtdata.subscribe_quote(code, period="tick", count=-1)
        except Exception as e:
            logger.error(f"subscribe failed: {e}")

    def get_history_df(
        self,
        codes: list[str],
        period: str = "1d",
        start_date: str = "",
        end_date: str = "",
        count: int = 0,
    ) -> dict[str, pd.DataFrame]:
        """Fetch historical OHLCV data as DataFrames for backtesting.

        Args:
            codes: List of stock/ETF codes
            period: Bar period ("1d", "1m", etc.)
            start_date: Start date "YYYYMMDD" (optional)
            end_date: End date "YYYYMMDD" (optional)
            count: Number of bars (used if start_date/end_date not set)

        Returns:
            Dict of {code: DataFrame} with columns [open, high, low, close, volume]
        """
        try:
            from xtquant import xtdata

            result: dict[str, pd.DataFrame] = {}
            xtdata.subscribe_quote(codes, period=period, count=-1)

            data = xtdata.get_market_data_ex(
                field_list=[],
                stock_list=codes,
                period=period,
                start_time=start_date if start_date else "",
                end_time=end_date if end_date else "",
                count=count if not start_date else 0,
            )

            for code in codes:
                if code in data and not data[code].empty:
                    df = data[code].copy()
                    # Ensure required columns exist
                    for col in ["open", "high", "low", "close", "volume"]:
                        if col not in df.columns:
                            logger.warning(f"Missing column {col} for {code}")
                            continue
                    result[code] = df[["open", "high", "low", "close", "volume"]]
                    logger.info(f"Loaded {code}: {len(result[code])} bars")

            return result
        except Exception as e:
            logger.error(f"get_history_df failed: {e}")
            return {}
