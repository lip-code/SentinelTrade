"""
SentinelTrade - Backtest Runner

Runs the ETF rotation strategy backtest using real historical data from xtquant.
Reads ETF pool and parameters from config.yaml.

Usage:
    # Run with real data (requires QMT):
    python backtest_run.py

    # Run with sample data:
    python backtest_run.py --sample

    # Specify date range:
    python backtest_run.py --start 20230101 --end 20250101

    # Run parameter optimization:
    python backtest_run.py --optimize
"""
from __future__ import annotations

import argparse
import sys

import backtrader as bt
import numpy as np
import pandas as pd
from loguru import logger

from src.backtest.backtest_engine import BacktestConfig, BacktestEngine
from src.backtest.plot import generate_html_report
from src.config.loader import load_config


class ETFRotationStrategy(bt.Strategy):
    """ETF Trend Rotation Strategy for Backtrader."""

    params = (
        ("ma_short", 5),
        ("ma_mid", 10),
        ("ma_long", 20),
        ("max_holdings", 3),
        ("trend_threshold", 0.02),
        ("rebalance_period", 5),
        ("position_pct", 0.30),
    )

    def __init__(self) -> None:
        self.indicators: dict[str, dict] = {}
        self._bar_count = 0

        for d in self.datas:
            name = d._name
            self.indicators[name] = {
                "ma5": bt.indicators.SMA(d.close, period=self.params.ma_short),
                "ma10": bt.indicators.SMA(d.close, period=self.params.ma_mid),
                "ma20": bt.indicators.SMA(d.close, period=self.params.ma_long),
            }

    def next(self) -> None:
        self._bar_count += 1
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

        for d in self.datas:
            name = d._name
            pos = self.getposition(d)
            if pos.size > 0 and name not in target_codes:
                self.close(d)

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


def load_sample_data(codes: list[str], days: int = 500) -> dict[str, pd.DataFrame]:
    """Generate sample data for testing without xtquant."""
    np.random.seed(42)
    data_feeds: dict[str, pd.DataFrame] = {}
    for i, code in enumerate(codes):
        dates = pd.date_range("2024-01-01", periods=days, freq="B")
        price = 4.0 + i * 0.5
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


def load_real_data(codes: list[str], qmt_path: str, start_date: str, end_date: str) -> dict[str, pd.DataFrame]:
    """Load real data from xtquant."""
    from src.market.xt_provider import XtProvider

    provider = XtProvider(qmt_path=qmt_path)
    if not provider.connect():
        logger.error("Failed to connect to xtdata")
        return {}

    data = provider.get_history_df(
        codes=codes,
        period="1d",
        start_date=start_date,
        end_date=end_date,
    )
    return data


def main():
    parser = argparse.ArgumentParser(description="SentinelTrade Backtest Runner")
    parser.add_argument("--sample", action="store_true", help="Use sample data instead of real")
    parser.add_argument("--start", default="20240101", help="Start date YYYYMMDD")
    parser.add_argument("--end", default="", help="End date YYYYMMDD")
    parser.add_argument("--days", type=int, default=500, help="Sample data days")
    parser.add_argument("--optimize", action="store_true", help="Run parameter optimization")
    parser.add_argument("--output", default="backtest_report.html", help="Output report path")
    args = parser.parse_args()

    # Load config
    config = load_config("config.yaml")
    etf_codes = [etf.code for etf in config.etf_pool]
    backtest_cfg = config.backtest

    print("=" * 60)
    print("SentinelTrade - ETF Rotation Backtest")
    print("=" * 60)

    # Load data
    print("\n[1] Loading data...")
    if args.sample:
        print("  Mode: Sample data")
        data_feeds = load_sample_data(etf_codes, days=args.days)
    else:
        print("  Mode: Real data from xtquant")
        data_feeds = load_real_data(
            codes=etf_codes,
            qmt_path=config.broker.qmt_path,
            start_date=args.start,
            end_date=args.end,
        )
        if not data_feeds:
            print("  WARNING: No real data, falling back to sample")
            data_feeds = load_sample_data(etf_codes, days=args.days)

    for code, df in data_feeds.items():
        print(f"  {code}: {len(df)} bars, {df.index[0].date()} ~ {df.index[-1].date()}")

    # Configure engine
    print("\n[2] Configuring engine...")
    engine_config = BacktestConfig(
        initial_cash=backtest_cfg.initial_cash,
        commission_rate=backtest_cfg.commission_rate,
        commission_min=backtest_cfg.commission_min,
        slippage_perc=backtest_cfg.slippage_perc,
        stamp_tax=backtest_cfg.stamp_tax,
    )
    engine = BacktestEngine(engine_config)

    strategy_params = {
        "ma_short": config.strategy.ma_periods[0] if config.strategy.ma_periods else 5,
        "ma_mid": config.strategy.ma_periods[1] if len(config.strategy.ma_periods) > 1 else 10,
        "ma_long": config.strategy.ma_periods[2] if len(config.strategy.ma_periods) > 2 else 20,
        "max_holdings": config.strategy.max_holdings,
        "trend_threshold": config.strategy.trend_threshold,
        "rebalance_period": 5,
        "position_pct": config.risk.max_position_ratio,
    }

    # Run backtest
    print("\n[3] Running backtest...")
    engine.setup(
        strategy_cls=ETFRotationStrategy,
        strategy_params=strategy_params,
        data_feeds=data_feeds,
        sizer_pct=0.0,
        sizer_stake=100,
    )
    report = engine.run()

    # Print results
    print("\n[4] Results:")
    print(report.summary())

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

    # Generate report
    print(f"\n[6] Generating report...")
    try:
        generate_html_report(report, args.output)
        print(f"  Report saved to: {args.output}")
    except Exception as e:
        print(f"  Report generation failed: {e}")

    # Optimization
    if args.optimize:
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
