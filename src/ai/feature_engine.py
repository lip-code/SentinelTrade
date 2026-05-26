"""Feature engineering for AI models."""
from __future__ import annotations

import numpy as np
import pandas as pd

from src.strategy.factor import ma, momentum, volatility


def extract_features(df: pd.DataFrame) -> np.ndarray:
    """Extract technical indicator features from OHLCV data."""
    close = df["close"]
    features = pd.DataFrame()
    features["ma5_ratio"] = close / ma(close, 5)
    features["ma10_ratio"] = close / ma(close, 10)
    features["ma20_ratio"] = close / ma(close, 20)
    features["momentum_5"] = momentum(close, 5)
    features["momentum_10"] = momentum(close, 10)
    features["volatility_10"] = volatility(close, 10)
    features["volatility_20"] = volatility(close, 20)
    return features.fillna(0).values
