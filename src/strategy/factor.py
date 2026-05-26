"""Factor calculation library for technical indicators."""
from __future__ import annotations

import numpy as np
import pandas as pd


def ma(series: pd.Series, period: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window=period, min_periods=1).mean()


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential moving average."""
    return series.ewm(span=period, adjust=False).mean()


def momentum(series: pd.Series, period: int) -> pd.Series:
    """Price momentum (rate of change)."""
    return series.pct_change(periods=period)


def volatility(series: pd.Series, period: int) -> pd.Series:
    """Rolling standard deviation (volatility)."""
    return series.rolling(window=period, min_periods=1).std()


def trend_strength(series: pd.Series, short: int, long: int) -> pd.Series:
    """Trend strength indicator: (MA_short - MA_long) / MA_long."""
    ma_short = ma(series, short)
    ma_long = ma(series, long)
    return (ma_short - ma_long) / ma_long.replace(0, np.nan)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)
    tr = pd.concat([
        high - low,
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=1).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = delta.where(delta > 0, 0).rolling(window=period, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period, min_periods=1).mean()
    rs = gain / loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))
