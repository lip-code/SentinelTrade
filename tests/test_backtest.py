"""Tests for the backtest module."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import backtrader as bt
from src.backtest.backtest_engine import AShareCommission, BacktestConfig, BacktestEngine, PandasDataFeed
from src.backtest.analyzer import TradeAnalyzer, TradeStats, SharpeAnalyzer, DrawDownAnalyzer, TradeRecord
from src.backtest.performance import PerformanceReport, build_performance_report


def _make_data(code: str = "510300", days: int = 100, start: float = 4.0) -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range("2024-01-01", periods=days, freq="B")
    returns = np.random.normal(0.0003, 0.015, days)
    prices = start * np.exp(np.cumsum(returns))
    return pd.DataFrame({
        "open": prices * (1 + np.random.uniform(-0.005, 0.005, days)),
        "high": prices * (1 + np.abs(np.random.normal(0, 0.01, days))),
        "low": prices * (1 - np.abs(np.random.normal(0, 0.01, days))),
        "close": prices,
        "volume": np.random.randint(100000, 1000000, days).astype(float),
    }, index=dates)


class BuyAndHoldStrategy(bt.Strategy):
    params = (("period", 10),)

    def __init__(self):
        self._bar = 0

    def next(self):
        self._bar += 1
        if self._bar == self.params.period:
            price = self.datas[0].close[0]
            shares = int(self.broker.getcash() * 0.9 / price / 100) * 100
            if shares > 0:
                self.buy(size=shares)


def test_commission_calculation():
    comm = AShareCommission(commission=0.0003, min_commission=5.0, stamp_tax=0.0)
    c1 = comm._getcommission(1000, 4.5, False)
    assert c1 == max(1000 * 4.5 * 0.0003, 5.0)

    c2 = comm._getcommission(100, 4.5, False)
    assert c2 == 5.0


def test_stamp_tax_on_sell():
    comm = AShareCommission(commission=0.0003, min_commission=5.0, stamp_tax=0.001)
    # Buy: no stamp tax
    c_buy = comm._getcommission(1000, 4.5, False)
    assert c_buy == max(1000 * 4.5 * 0.0003, 5.0)
    # Sell: stamp tax added
    c_sell = comm._getcommission(-1000, 4.5, False)
    expected = max(1000 * 4.5 * 0.0003, 5.0) + 1000 * 4.5 * 0.001
    assert abs(c_sell - expected) < 0.01


def test_backtest_engine_runs():
    config = BacktestConfig(initial_cash=30000.0, commission_rate=0.0003, slippage_perc=0.001)
    engine = BacktestEngine(config)
    data = _make_data()
    engine.setup(BuyAndHoldStrategy, {"period": 10}, {"510300": data})
    report = engine.run()

    assert isinstance(report, PerformanceReport)
    assert report.initial_cash == 30000.0
    assert report.final_value > 0
    assert len(report.equity_curve) > 0


def test_performance_report_summary():
    config = BacktestConfig(initial_cash=30000.0)
    engine = BacktestEngine(config)
    data = _make_data()
    engine.setup(BuyAndHoldStrategy, {"period": 5}, {"510300": data})
    report = engine.run()

    summary = report.summary()
    assert "BACKTEST PERFORMANCE REPORT" in summary
    assert "30,000" in summary


def test_performance_report_to_dict():
    config = BacktestConfig(initial_cash=30000.0)
    engine = BacktestEngine(config)
    data = _make_data()
    engine.setup(BuyAndHoldStrategy, {"period": 5}, {"510300": data})
    report = engine.run()

    d = report.to_dict()
    assert "initial_cash" in d
    assert "total_return" in d
    assert "sharpe_ratio" in d


def test_multi_etf_backtest():
    data_feeds = {
        "510300": _make_data("510300", 100, 4.0),
        "510500": _make_data("510500", 100, 5.0),
        "159915": _make_data("159915", 100, 3.0),
    }
    config = BacktestConfig(initial_cash=30000.0)
    engine = BacktestEngine(config)
    engine.setup(BuyAndHoldStrategy, {"period": 10}, data_feeds)
    report = engine.run()

    assert report.final_value > 0
    assert len(report.equity_curve) > 0


def test_trade_stats_empty():
    stats = TradeStats()
    assert stats.total_trades == 0
    assert stats.win_rate == 0.0


def test_drawdown_values():
    config = BacktestConfig(initial_cash=30000.0)
    engine = BacktestEngine(config)
    data = _make_data()
    engine.setup(BuyAndHoldStrategy, {"period": 5}, {"510300": data})
    report = engine.run()

    assert report.max_drawdown >= 0
    assert report.max_drawdown <= 1.0
    assert len(report.drawdown_curve) == len(report.equity_curve)
