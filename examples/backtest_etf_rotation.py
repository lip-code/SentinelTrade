"""
Complete example: ETF Rotation Strategy Backtest

This example demonstrates:
1. Loading historical ETF data (real from xtquant or sample)
2. Implementing a Backtrader strategy with MA-based trend following
3. Running a backtest with commission and slippage
4. Analyzing results with performance report
5. Generating interactive charts
6. Running parameter optimization

Usage:
    # With sample data (no xtquant needed):
    python examples/backtest_etf_rotation.py

    # With real data from xtquant (requires QMT installed):
    python examples/backtest_etf_rotation.py --real --start 20240101 --end 20250101
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import backtrader as bt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backtest.backtest_engine import BacktestConfig, BacktestEngine
from src.backtest.performance import PerformanceReport
from src.backtest.plot import (
    generate_html_report,
    plot_equity_curve,
    plot_trade_distribution,
    plot_monthly_returns,
)


# ============================================================================
# Strategy Implementation
# ============================================================================

class ETFRotationStrategy(bt.Strategy):
    """ETF Trend Rotation Strategy for Backtrader.

    Logic:
    1. Calculate MA5, MA10, MA20 for each ETF
    2. Score trend strength: (MA5 - MA20) / MA20
    3. Only consider ETFs in uptrend (close > MA20, MA5 > MA10)
    4. Buy top N by trend strength
    5. Sell when ETF falls out of top N or trend reverses
    """

    params = (
        ("ma_short", 5),
        ("ma_mid", 10),
        ("ma_long", 20),
        ("max_holdings", 3),
        ("trend_threshold", 0.02),
        ("rebalance_period", 5),  # Rebalance every N bars
        ("position_pct", 0.30),   # Max % of portfolio per position
    )

    def __init__(self) -> None:
        self.indicators: dict[str, dict] = {}
        self._bar_count = 0
        self._equity_curve: list[float] = []

        for d in self.datas:
            name = d._name
            self.indicators[name] = {
                "ma5": bt.indicators.SMA(d.close, period=self.params.ma_short),
                "ma10": bt.indicators.SMA(d.close, period=self.params.ma_mid),
                "ma20": bt.indicators.SMA(d.close, period=self.params.ma_long),
            }

    def next(self) -> None:
        self._bar_count += 1
        self._equity_curve.append(self.broker.getvalue())

        if self._bar_count % self.params.rebalance_period != 0:
            return

        scores: dict[str, float] = {}
        for d in self.datas:
            name = d._name
            close = d.close[0]
            ma5 = self.indicators[name]["ma5"][0]
            ma10 = self.indicators[name]["ma10"][0]
            ma20 = self.indicators[name]["ma20"][0]

            if ma20 <= 0 or close <= 0:
                continue

            in_uptrend = close > ma20 and ma5 > ma10
            if in_uptrend:
                trend_strength = (ma5 - ma20) / ma20
                if trend_strength > self.params.trend_threshold:
                    scores[name] = trend_strength

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        target_codes = {code for code, _ in ranked[: self.params.max_holdings]}

        # Sell positions no longer in top
        for d in self.datas:
            name = d._name
            pos = self.getposition(d)
            if pos.size > 0 and name not in target_codes:
                self.close(d)

        # Buy new top-ranked ETFs
        cash = self.broker.getcash()
        for code, score in ranked[: self.params.max_holdings]:
            data = self.getdatabyname(code)
            pos = self.getposition(data)
            if pos.size == 0:
                price = data.close[0]
                if price > 0:
                    max_value = self.broker.getvalue() * self.params.position_pct
                    shares = int(max_value / price / 100) * 100
                    if shares > 0 and cash >= shares * price:
                        self.buy(data, size=shares)
                        cash -= shares * price


# ============================================================================
# Data Generation (replace with real data from xtquant)
# ============================================================================

def generate_sample_data(
    codes: list[str],
    days: int = 500,
    start_price: float = 4.0,
    seed: int = 42,
) -> dict[str, pd.DataFrame]:
    """Generate sample OHLCV data for testing."""
    np.random.seed(seed)
    data_feeds: dict[str, pd.DataFrame] = {}

    for i, code in enumerate(codes):
        dates = pd.date_range("2024-01-01", periods=days, freq="B")
        price = start_price + i * 0.5

        returns = np.random.normal(0.0003, 0.015, days)
        prices = price * np.exp(np.cumsum(returns))

        df = pd.DataFrame({
            "open": prices * (1 + np.random.uniform(-0.005, 0.005, days)),
            "high": prices * (1 + np.abs(np.random.normal(0, 0.01, days))),
            "low": prices * (1 - np.abs(np.random.normal(0, 0.01, days))),
            "close": prices,
            "volume": np.random.randint(500000, 5000000, days).astype(float),
        }, index=dates)

        data_feeds[code] = df

    return data_feeds


def load_real_data(
    codes: list[str],
    qmt_path: str = "",
    start_date: str = "20240101",
    end_date: str = "",
    count: int = 500,
) -> dict[str, pd.DataFrame]:
    """Load real historical data from xtquant.

    Requires QMT mini terminal installed and xtquant package.

    Args:
        codes: List of ETF codes
        qmt_path: Path to QMT installation (empty = auto-detect)
        start_date: Start date "YYYYMMDD"
        end_date: End date "YYYYMMDD" (empty = up to latest)
        count: Number of bars (used if start_date not set)

    Returns:
        Dict of {code: DataFrame} with OHLCV columns
    """
    from src.market.xt_provider import XtProvider

    provider = XtProvider(qmt_path=qmt_path)
    if not provider.connect():
        print("ERROR: Failed to connect to xtdata. Is QMT installed?")
        return {}

    data = provider.get_history_df(
        codes=codes,
        period="1d",
        start_date=start_date,
        end_date=end_date,
        count=count,
    )

    if not data:
        print("ERROR: No data returned from xtdata")
    else:
        total_bars = sum(len(df) for df in data.values())
        print(f"  Loaded {len(data)} ETFs, {total_bars} total bars")

    return data


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="ETF Rotation Backtest")
    parser.add_argument("--real", action="store_true", help="Use real data from xtquant")
    parser.add_argument("--start", default="20240101", help="Start date YYYYMMDD")
    parser.add_argument("--end", default="", help="End date YYYYMMDD")
    parser.add_argument("--days", type=int, default=500, help="Sample data days (if not --real)")
    parser.add_argument("--qmt-path", default="", help="QMT installation path")
    args = parser.parse_args()

    print("=" * 60)
    print("SentinelTrade - ETF Rotation Backtest")
    print("=" * 60)

    etf_codes = ["510300", "510500", "159915", "512100", "159941", "518880", "511010"]

    # 1. Load data
    print("\n[1] Loading data...")
    if args.real:
        print("  Mode: Real data from xtquant")
        data_feeds = load_real_data(
            codes=etf_codes,
            qmt_path=args.qmt_path,
            start_date=args.start,
            end_date=args.end,
        )
        if not data_feeds:
            print("  Falling back to sample data")
            data_feeds = generate_sample_data(etf_codes, days=args.days)
    else:
        print("  Mode: Sample data")
        data_feeds = generate_sample_data(etf_codes, days=args.days)

    for code, df in data_feeds.items():
        print(f"  {code}: {len(df)} bars, {df.index[0].date()} ~ {df.index[-1].date()}")

    # 2. Configure engine
    print("\n[2] Configuring engine...")
    config = BacktestConfig(
        initial_cash=30000.0,
        commission_rate=0.0003,
        commission_min=5.0,
        slippage_perc=0.001,
        stamp_tax=0.0,
    )
    engine = BacktestEngine(config)

    # 3. Setup and run
    print("\n[3] Running backtest...")
    engine.setup(
        strategy_cls=ETFRotationStrategy,
        strategy_params={
            "ma_short": 5,
            "ma_mid": 10,
            "ma_long": 20,
            "max_holdings": 3,
            "trend_threshold": 0.02,
            "rebalance_period": 5,
            "position_pct": 0.30,
        },
        data_feeds=data_feeds,
        sizer_pct=0.0,  # Strategy handles sizing
        sizer_stake=100,
    )

    report = engine.run()

    # 4. Print results
    print("\n[4] Results:")
    print(report.summary())

    # 5. Trade log
    if report.trade_log:
        print(f"\n[5] Trade Log ({len(report.trade_log)} trades):")
        print(f"{'Code':<10} {'Dir':<6} {'Price':>8} {'Size':>6} {'P&L':>10} {'Bars':>5}")
        print("-" * 50)
        for t in report.trade_log[:20]:
            print(
                f"{t['code']:<10} {t['direction']:<6} "
                f"{t['price']:>8.3f} {t['size']:>6d} "
                f"{t['pnl']:>10.2f} {t['bar_count']:>5d}"
            )
        if len(report.trade_log) > 20:
            print(f"  ... and {len(report.trade_log) - 20} more trades")

    # 6. Generate charts
    print("\n[6] Generating charts...")
    try:
        generate_html_report(report, "backtest_report.html")
        print("  HTML report saved to: backtest_report.html")
    except Exception as e:
        print(f"  Chart generation failed: {e}")

    # 7. Parameter optimization
    print("\n[7] Running parameter optimization...")
    opt_results = engine.optimize(
        strategy_cls=ETFRotationStrategy,
        data_feeds=data_feeds,
        param_grid={
            "ma_short": [3, 5, 8],
            "ma_long": [15, 20, 25],
            "max_holdings": [2, 3],
        },
        maximize="sharpe",
    )

    if opt_results:
        print(f"\nTop 5 parameter combinations by Sharpe:")
        print(f"{'MA_Short':>8} {'MA_Long':>8} {'Holdings':>8} {'Sharpe':>8} {'Return':>10} {'MaxDD':>8}")
        print("-" * 55)
        for r in opt_results[:5]:
            p = r["params"]
            print(
                f"{p.get('ma_short', 0):>8d} {p.get('ma_long', 0):>8d} "
                f"{p.get('max_holdings', 0):>8d} {r['sharpe']:>8.4f} "
                f"{r['total_return']:>10.2%} {r['max_drawdown']:>8.2%}"
            )

    print("\nDone!")


if __name__ == "__main__":
    main()
