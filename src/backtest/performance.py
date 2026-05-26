"""
Performance report generation for backtest results.

Aggregates analyzer outputs into a single structured report
with all key metrics: returns, drawdown, Sharpe, trade stats.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import backtrader as bt
import numpy as np

from src.backtest.analyzer import TradeStats


@dataclass
class PerformanceReport:
    """Complete backtest performance report."""

    # Capital
    initial_cash: float = 0.0
    final_value: float = 0.0
    total_return: float = 0.0
    annual_return: float = 0.0

    # Risk
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    annual_volatility: float = 0.0
    sharpe_ratio: float = 0.0
    calmar_ratio: float = 0.0

    # Trades
    total_trades: int = 0
    won_trades: int = 0
    lost_trades: int = 0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    max_win: float = 0.0
    max_loss: float = 0.0
    profit_factor: float = 0.0
    avg_bars_held: float = 0.0
    total_commission: float = 0.0

    # Equity curve
    equity_curve: list[float] = field(default_factory=list)
    daily_returns: list[float] = field(default_factory=list)
    drawdown_curve: list[float] = field(default_factory=list)

    # Trade log
    trade_log: list[dict[str, Any]] = field(default_factory=list)

    def summary(self) -> str:
        """Return a formatted summary string."""
        lines = [
            "=" * 60,
            "BACKTEST PERFORMANCE REPORT",
            "=" * 60,
            f"Initial Cash:       {self.initial_cash:>14,.2f}",
            f"Final Value:        {self.final_value:>14,.2f}",
            f"Total Return:        {self.total_return:>11.2%}",
            f"Annual Return:       {self.annual_return:>11.2%}",
            "-" * 60,
            f"Max Drawdown:        {self.max_drawdown:>11.2%}",
            f"Max DD Duration:     {self.max_drawdown_duration:>8d} bars",
            f"Annual Volatility:   {self.annual_volatility:>11.2%}",
            f"Sharpe Ratio:        {self.sharpe_ratio:>11.4f}",
            f"Calmar Ratio:        {self.calmar_ratio:>11.4f}",
            "-" * 60,
            f"Total Trades:        {self.total_trades:>8d}",
            f"Won / Lost:          {self.won_trades:>4d} / {self.lost_trades:>4d}",
            f"Win Rate:            {self.win_rate:>11.2%}",
            f"Avg Win:             {self.avg_win:>14,.2f}",
            f"Avg Loss:            {self.avg_loss:>14,.2f}",
            f"Max Win:             {self.max_win:>14,.2f}",
            f"Max Loss:            {self.max_loss:>14,.2f}",
            f"Profit Factor:       {self.profit_factor:>11.4f}",
            f"Avg Bars Held:       {self.avg_bars_held:>11.1f}",
            f"Total Commission:    {self.total_commission:>14,.2f}",
            "=" * 60,
        ]
        return "\n".join(lines)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "initial_cash": self.initial_cash,
            "final_value": self.final_value,
            "total_return": self.total_return,
            "annual_return": self.annual_return,
            "max_drawdown": self.max_drawdown,
            "sharpe_ratio": self.sharpe_ratio,
            "calmar_ratio": self.calmar_ratio,
            "total_trades": self.total_trades,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "total_commission": self.total_commission,
        }


def build_performance_report(cerebro: bt.Cerebro, results: list) -> PerformanceReport:
    """Build a PerformanceReport from a completed Backtrader run."""
    strat = results[0]

    # Extract from built-in analyzers
    sharpe_analysis = strat.analyzers.sharpe.get_analysis()
    drawdown_analysis = strat.analyzers.drawdown.get_analysis()
    returns_analysis = strat.analyzers.returns.get_analysis()

    # Extract from custom analyzer
    trade_detail = strat.analyzers.trade_detail.get_analysis()

    # Equity curve from strategy
    equity_curve = []
    if hasattr(strat, "_equity_curve"):
        equity_curve = strat._equity_curve
    else:
        initial = cerebro.broker.startingcash
        final = cerebro.broker.getvalue()
        equity_curve = [initial, final]

    # Drawdown curve
    drawdown_curve = []
    if equity_curve:
        peak = equity_curve[0]
        for val in equity_curve:
            peak = max(peak, val)
            dd = (peak - val) / peak if peak > 0 else 0
            drawdown_curve.append(dd)

    # Daily returns
    daily_returns = []
    if len(equity_curve) > 1:
        arr = np.array(equity_curve)
        daily_returns = (np.diff(arr) / arr[:-1]).tolist()

    # Metrics from analyzers
    ts = trade_detail if isinstance(trade_detail, TradeStats) else TradeStats()

    # bt.analyzers.Returns: rtot = total log return
    log_return = returns_analysis.get("rtot", 0)
    total_return = np.exp(log_return) - 1 if log_return else 0

    # bt.analyzers.DrawDown: max.drawdown is percentage (0-100)
    max_dd_info = drawdown_analysis.get("max", {})
    max_dd = max_dd_info.get("drawdown", 0) / 100 if isinstance(max_dd_info, dict) else 0
    max_dd_len = max_dd_info.get("len", 0) if isinstance(max_dd_info, dict) else 0

    # bt.analyzers.SharpeRatio: sharperatio
    sharpe = sharpe_analysis.get("sharperatio", 0) or 0

    # Annual return
    n_days = len(equity_curve)
    annual_return = (1 + total_return) ** (252 / max(n_days, 1)) - 1 if n_days > 0 else 0

    # Annual volatility from daily returns
    annual_vol = float(np.std(daily_returns) * np.sqrt(252)) if daily_returns else 0

    # Calmar ratio
    calmar = annual_return / max_dd if max_dd > 0 else 0

    # Build trade log
    trade_log = []
    if isinstance(ts, TradeStats):
        for t in ts.trades:
            trade_log.append({
                "code": t.code,
                "direction": t.direction,
                "price": t.price,
                "size": t.size,
                "pnl": t.pnl,
                "pnl_pct": t.pnl_pct,
                "commission": t.commission,
                "bar_count": t.bar_count,
                "dt": t.dt.isoformat() if t.dt else "",
            })

    report = PerformanceReport(
        initial_cash=cerebro.broker.startingcash,
        final_value=cerebro.broker.getvalue(),
        total_return=total_return,
        annual_return=annual_return,
        max_drawdown=max_dd,
        max_drawdown_duration=max_dd_len,
        annual_volatility=annual_vol,
        sharpe_ratio=sharpe,
        calmar_ratio=calmar,
        total_trades=ts.total_trades,
        won_trades=ts.won_trades,
        lost_trades=ts.lost_trades,
        win_rate=ts.win_rate,
        avg_win=ts.avg_win,
        avg_loss=ts.avg_loss,
        max_win=ts.max_win,
        max_loss=ts.max_loss,
        profit_factor=ts.profit_factor,
        avg_bars_held=ts.avg_bars_held,
        total_commission=ts.total_commission,
        equity_curve=equity_curve,
        daily_returns=daily_returns,
        drawdown_curve=drawdown_curve,
        trade_log=trade_log,
    )

    return report
