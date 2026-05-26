"""
Backtest engine wrapping Backtrader with A-share ETF support.

Features:
- Commission (percentage + minimum)
- Slippage (percentage or fixed)
- Position sizing (percentage of portfolio or fixed volume)
- Multi-ETF support
- Strategy parameter optimization
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import backtrader as bt
import pandas as pd
from loguru import logger

from src.backtest.analyzer import (
    DrawDownAnalyzer,
    SharpeAnalyzer,
    TradeAnalyzer,
    ReturnsAnalyzer,
)
from src.backtest.performance import PerformanceReport, build_performance_report


@dataclass
class BacktestConfig:
    initial_cash: float = 30000.0
    commission_rate: float = 0.0003
    commission_min: float = 5.0
    slippage_perc: float = 0.001
    stamp_tax: float = 0.0
    start_date: str = ""
    end_date: str = ""


class AShareCommission(bt.CommInfoBase):
    """A-share commission: percentage with minimum, plus stamp tax on sells."""

    params = (
        ("commission", 0.0003),
        ("min_commission", 5.0),
        ("stamp_tax", 0.0),
        ("stocklike", True),
        ("commtype", bt.CommInfoBase.COMM_PERC),
    )

    def _getcommission(self, size, price, pseudoexec):
        turnover = abs(size) * price
        commission = turnover * self.p.commission
        commission = max(commission, self.p.min_commission)
        if size < 0:
            commission += turnover * self.p.stamp_tax
        return commission


class SlippageScheme(bt.CommInfoBase):
    """Slippage model: percentage-based."""

    params = (
        ("slippage", 0.001),
        ("percabs", True),
    )


class PandasDataFeed(bt.feeds.PandasData):
    """Backtrader data feed from pandas DataFrame."""

    params = (
        ("datetime", None),
        ("open", "open"),
        ("high", "high"),
        ("low", "low"),
        ("close", "close"),
        ("volume", "volume"),
        ("openinterest", -1),
    )


class PositionSizer(bt.Sizer):
    """Position sizer: buy fixed number of shares (multiple of 100)."""

    params = (
        ("stake", 100),
        ("pct", 0.0),
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        if self.p.pct > 0:
            price = data.close[0]
            if price <= 0:
                return 0
            target_value = cash * self.p.pct
            shares = int(target_value / price / 100) * 100
            return max(shares, 0)
        return self.p.stake


class BacktestEngine:
    """Main backtest engine wrapping Backtrader."""

    def __init__(self, config: BacktestConfig | None = None) -> None:
        self._config = config or BacktestConfig()
        self._cerebro: bt.Cerebro | None = None
        self._results: list = []
        self._strategies: list = []

    @property
    def config(self) -> BacktestConfig:
        return self._config

    def setup(
        self,
        strategy_cls: type[bt.Strategy],
        strategy_params: dict[str, Any] | None = None,
        data_feeds: dict[str, pd.DataFrame] | None = None,
        sizer_pct: float = 0.0,
        sizer_stake: int = 100,
    ) -> None:
        """Configure the backtest engine.

        Args:
            strategy_cls: Backtrader Strategy class
            strategy_params: Parameters to pass to the strategy
            data_feeds: Dict of {code: DataFrame} with columns [open, high, low, close, volume]
            sizer_pct: Position size as percentage of portfolio (0 = use fixed stake)
            sizer_stake: Fixed number of shares per trade
        """
        self._cerebro = bt.Cerebro()

        self._cerebro.broker.setcash(self._config.initial_cash)

        commission_info = AShareCommission(
            commission=self._config.commission_rate,
            min_commission=self._config.commission_min,
            stamp_tax=self._config.stamp_tax,
        )
        self._cerebro.broker.addcommissioninfo(commission_info)

        if self._config.slippage_perc > 0:
            self._cerebro.broker.set_slippage_perc(self._config.slippage_perc)

        self._cerebro.addsizer(PositionSizer, pct=sizer_pct, stake=sizer_stake)

        if data_feeds:
            for code, df in data_feeds.items():
                feed = PandasDataFeed(dataname=df, name=code)
                self._cerebro.adddata(feed)

        params = strategy_params or {}
        self._cerebro.addstrategy(strategy_cls, **params)

        self._cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", riskfreerate=0.02)
        self._cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")
        self._cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
        self._cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
        self._cerebro.addanalyzer(TradeAnalyzer, _name="trade_detail")

        logger.info(
            f"Backtest setup: cash={self._config.initial_cash}, "
            f"commission={self._config.commission_rate}, slippage={self._config.slippage_perc}"
        )

    def run(self) -> PerformanceReport:
        """Run the backtest and return performance report."""
        if self._cerebro is None:
            raise RuntimeError("Engine not configured. Call setup() first.")

        logger.info(f"Starting backtest with ¥{self._config.initial_cash:,.2f}")
        self._results = self._cerebro.run()
        self._strategies = self._results

        final_value = self._cerebro.broker.getvalue()
        logger.info(f"Backtest finished. Final value: ¥{final_value:,.2f}")

        return build_performance_report(self._cerebro, self._results)

    def optimize(
        self,
        strategy_cls: type[bt.Strategy],
        data_feeds: dict[str, pd.DataFrame],
        param_grid: dict[str, list],
        maximize: str = "sharpe",
        max_combinations: int = 100,
    ) -> list[dict[str, Any]]:
        """Run strategy parameter optimization (sequential, Windows-safe).

        Args:
            strategy_cls: Backtrader Strategy class
            data_feeds: Dict of {code: DataFrame}
            param_grid: Dict of {param_name: [values]} to search
            maximize: Metric to maximize ("sharpe", "return", "drawdown")
            max_combinations: Maximum number of parameter combinations

        Returns:
            List of dicts with params and results, sorted by target metric
        """
        import itertools

        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))[:max_combinations]

        logger.info(f"Running optimization: {len(combinations)} combinations")

        results = []
        for i, combo in enumerate(combinations):
            params = dict(zip(keys, combo))
            cerebro = bt.Cerebro()
            cerebro.broker.setcash(self._config.initial_cash)
            cerebro.broker.addcommissioninfo(
                AShareCommission(
                    commission=self._config.commission_rate,
                    min_commission=self._config.commission_min,
                    stamp_tax=self._config.stamp_tax,
                )
            )
            if self._config.slippage_perc > 0:
                cerebro.broker.set_slippage_perc(self._config.slippage_perc)

            for code, df in data_feeds.items():
                feed = PandasDataFeed(dataname=df, name=code)
                cerebro.adddata(feed)

            cerebro.addstrategy(strategy_cls, **params)
            cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name="sharpe", riskfreerate=0.02)
            cerebro.addanalyzer(bt.analyzers.Returns, _name="returns")
            cerebro.addanalyzer(bt.analyzers.DrawDown, _name="drawdown")

            try:
                run_results = cerebro.run()
                strat = run_results[0]
                sharpe = strat.analyzers.sharpe.get_analysis().get("sharperatio", 0) or 0
                total_return = strat.analyzers.returns.get_analysis().get("rtot", 0)
                max_dd = strat.analyzers.drawdown.get_analysis().get("max", {}).get("drawdown", 0)

                results.append({
                    "params": params,
                    "sharpe": sharpe,
                    "total_return": total_return,
                    "max_drawdown": max_dd / 100 if max_dd > 1 else max_dd,
                })
            except Exception as e:
                logger.warning(f"Combination {params} failed: {e}")

            if (i + 1) % 10 == 0:
                logger.info(f"  Progress: {i + 1}/{len(combinations)}")

        reverse = maximize != "drawdown"
        results.sort(key=lambda x: x.get(maximize, 0), reverse=reverse)

        logger.info(f"Optimization complete: {len(results)} results")
        return results

        reverse = maximize != "drawdown"
        results.sort(key=lambda x: x.get(maximize, 0), reverse=reverse)

        logger.info(f"Optimization complete: {len(results)} results")
        return results[:max_combinations]

    def plot(self, style: str = "candle", **kwargs) -> None:
        """Plot backtest results."""
        if self._cerebro is None:
            raise RuntimeError("No results to plot. Run backtest first.")
        try:
            self._cerebro.plot(style=style, **kwargs)
        except Exception as e:
            logger.warning(f"Plot failed (may need display): {e}")

    @property
    def cerebro(self) -> bt.Cerebro | None:
        return self._cerebro

    @property
    def strategy(self) -> bt.Strategy | None:
        return self._strategies[0] if self._strategies else None
