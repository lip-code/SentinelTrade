"""ETF Trend Rotation Strategy.

Core logic:
1. Calculate MA5, MA10, MA20 for each ETF
2. Score trend strength: (MA5 - MA20) / MA20
3. Only consider ETFs in uptrend (close > MA20, MA5 > MA10)
4. Buy top N by trend strength
5. Sell when ETF falls out of top N or trend reverses
"""
from __future__ import annotations

from dataclasses import dataclass, field

from loguru import logger

from src.common.enums import Direction, SignalType
from src.common.types import Bar, Signal
from src.strategy.signal import SignalStrength, StrategySignal
from src.strategy.strategy_base import Strategy


@dataclass
class ETFRotationParams:
    ma_periods: list[int] = field(default_factory=lambda: [5, 10, 20])
    trend_threshold: float = 0.02
    max_holdings: int = 3
    rebalance_days: list[int] = field(default_factory=lambda: [0, 4])


class ETFRotationStrategy(Strategy):
    """ETF trend rotation strategy with MA-based scoring."""

    def __init__(self, params: ETFRotationParams | None = None) -> None:
        self._params = params or ETFRotationParams()
        self._holdings: set[str] = set()
        self._history: dict[str, list[float]] = {}

    def on_bar(self, bars: dict[str, Bar]) -> list[Signal]:
        signals: list[Signal] = []
        scores: dict[str, float] = {}
        bar_data: dict[str, Bar] = {}

        for code, bar in bars.items():
            if bar.close <= 0:
                continue
            bar_data[code] = bar

            if code not in self._history:
                self._history[code] = []
            self._history[code].append(bar.close)

            score = self._calc_trend_score(code)
            if score is not None:
                scores[code] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_codes: set[str] = set()
        for code, score in ranked[: self._params.max_holdings]:
            if score > self._params.trend_threshold:
                top_codes.add(code)

        # Buy new top-ranked ETFs
        for code in top_codes - self._holdings:
            if code in bar_data:
                signals.append(StrategySignal(
                    code=code,
                    direction=Direction.BUY,
                    signal_type=SignalType.ENTRY,
                    strength=SignalStrength.STRONG.value,
                    price=bar_data[code].close,
                    source="etf_rotation",
                    trend_score=scores.get(code, 0),
                ))

        # Sell ETFs no longer in top
        for code in self._holdings - top_codes:
            if code in bar_data:
                signals.append(StrategySignal(
                    code=code,
                    direction=Direction.SELL,
                    signal_type=SignalType.EXIT,
                    strength=SignalStrength.STRONG.value,
                    price=bar_data[code].close,
                    source="etf_rotation",
                ))

        self._holdings = top_codes
        return signals

    def _calc_trend_score(self, code: str) -> float | None:
        """Calculate trend strength score for an ETF."""
        prices = self._history.get(code, [])
        if len(prices) < self._params.ma_periods[-1]:
            return None

        ma_short = sum(prices[-self._params.ma_periods[0]:]) / self._params.ma_periods[0]
        ma_long = sum(prices[-self._params.ma_periods[-1]:]) / self._params.ma_periods[-1]
        close = prices[-1]

        if ma_long <= 0 or close <= 0:
            return None

        # Check uptrend: close > MA_long and MA_short > MA_mid
        if len(prices) >= self._params.ma_periods[1]:
            ma_mid = sum(prices[-self._params.ma_periods[1]:]) / self._params.ma_periods[1]
            if close < ma_long or ma_short < ma_mid:
                return -1.0  # Not in uptrend

        return (ma_short - ma_long) / ma_long

    def update_holdings(self, codes: set[str]) -> None:
        self._holdings = codes

    def get_params(self) -> dict:
        return {
            "ma_periods": self._params.ma_periods,
            "trend_threshold": self._params.trend_threshold,
            "max_holdings": self._params.max_holdings,
            "rebalance_days": self._params.rebalance_days,
        }

    def update_params(self, params: dict) -> None:
        for k, v in params.items():
            if hasattr(self._params, k):
                setattr(self._params, k, v)
