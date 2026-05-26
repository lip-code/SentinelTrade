"""
Custom Backtrader analyzers for A-share ETF backtesting.

Provides detailed trade tracking, drawdown analysis, Sharpe ratio,
and return metrics beyond what built-in analyzers offer.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime

import backtrader as bt
import numpy as np


@dataclass
class TradeRecord:
    """Single trade record."""
    code: str = ""
    direction: str = ""
    price: float = 0.0
    size: int = 0
    value: float = 0.0
    commission: float = 0.0
    pnl: float = 0.0
    pnl_pct: float = 0.0
    dt: datetime | None = None
    bar_count: int = 0


@dataclass
class TradeStats:
    """Aggregated trade statistics."""
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
    total_pnl: float = 0.0
    total_commission: float = 0.0
    trades: list[TradeRecord] = field(default_factory=list)


class TradeAnalyzer(bt.Analyzer):
    """Custom analyzer that records every closed trade with details."""

    def __init__(self) -> None:
        self.trades: list[TradeRecord] = []
        self._trade_opened: dict[int, dict] = {}

    def notify_trade(self, trade):
        if trade.isopen:
            self._trade_opened[trade.ref] = {
                "code": trade.data._name,
                "dt_open": self.datas[0].datetime.datetime(0),
                "price_open": trade.price,
                "size": trade.size,
                "direction": "long" if trade.size > 0 else "short",
                "commission_open": trade.commission,
            }
        if trade.isclosed:
            opened = self._trade_opened.pop(trade.ref, {})
            direction = opened.get("direction", "long")
            open_size = abs(opened.get("size", 0))
            record = TradeRecord(
                code=trade.data._name,
                direction=direction,
                price=trade.price,
                size=open_size,
                value=abs(trade.value),
                commission=trade.commission,
                pnl=trade.pnl,
                pnl_pct=trade.pnlcomm / max(abs(trade.value), 1) * 100 if trade.value else 0,
                dt=self.datas[0].datetime.datetime(0),
                bar_count=trade.barlen or 0,
            )
            self.trades.append(record)

    def get_analysis(self) -> TradeStats:
        if not self.trades:
            return TradeStats()

        won = [t for t in self.trades if t.pnl > 0]
        lost = [t for t in self.trades if t.pnl <= 0]
        total_win = sum(t.pnl for t in won)
        total_loss = sum(t.pnl for t in lost)

        return TradeStats(
            total_trades=len(self.trades),
            won_trades=len(won),
            lost_trades=len(lost),
            win_rate=len(won) / len(self.trades) if self.trades else 0,
            avg_win=total_win / len(won) if won else 0,
            avg_loss=total_loss / len(lost) if lost else 0,
            max_win=max((t.pnl for t in won), default=0),
            max_loss=min((t.pnl for t in lost), default=0),
            profit_factor=abs(total_win / total_loss) if total_loss != 0 else float("inf"),
            avg_bars_held=sum(t.bar_count for t in self.trades) / len(self.trades),
            total_pnl=sum(t.pnl for t in self.trades),
            total_commission=sum(t.commission for t in self.trades),
            trades=self.trades,
        )


class SharpeAnalyzer(bt.Analyzer):
    """Annualized Sharpe ratio analyzer with daily returns."""

    def __init__(self) -> None:
        self._values: list[float] = []

    def next(self):
        self._values.append(self.strategy.broker.getvalue())

    def get_analysis(self) -> dict:
        if len(self._values) < 2:
            return {"sharpe": 0.0, "annual_return": 0.0, "annual_volatility": 0.0}

        values = np.array(self._values)
        daily_returns = np.diff(values) / values[:-1]
        annual_return = np.mean(daily_returns) * 252
        annual_vol = np.std(daily_returns) * np.sqrt(252)
        sharpe = (annual_return - 0.02) / annual_vol if annual_vol > 0 else 0

        return {
            "sharpe": float(sharpe),
            "annual_return": float(annual_return),
            "annual_volatility": float(annual_vol),
        }


class DrawDownAnalyzer(bt.Analyzer):
    """Detailed drawdown analyzer."""

    def __init__(self) -> None:
        self._values: list[float] = []
        self._max_dd: float = 0.0
        self._max_dd_duration: int = 0
        self._current_dd_duration: int = 0

    def next(self):
        value = self.strategy.broker.getvalue()
        self._values.append(value)

        peak = max(self._values)
        dd = (peak - value) / peak if peak > 0 else 0

        if dd > 0:
            self._current_dd_duration += 1
            self._max_dd_duration = max(self._max_dd_duration, self._current_dd_duration)
        else:
            self._current_dd_duration = 0

        self._max_dd = max(self._max_dd, dd)

    def get_analysis(self) -> dict:
        return {
            "max_drawdown": self._max_dd,
            "max_drawdown_duration": self._max_dd_duration,
            "final_value": self._values[-1] if self._values else 0,
        }


class ReturnsAnalyzer(bt.Analyzer):
    """Detailed returns analyzer."""

    def __init__(self) -> None:
        self._values: list[float] = []
        self._initial: float = 0

    def start(self):
        self._initial = self.strategy.broker.getvalue()

    def next(self):
        self._values.append(self.strategy.broker.getvalue())

    def get_analysis(self) -> dict:
        if not self._values:
            return {"total_return": 0, "annual_return": 0, "daily_returns": []}

        final = self._values[-1]
        total_return = (final - self._initial) / self._initial if self._initial > 0 else 0
        n_days = len(self._values)
        annual_return = (1 + total_return) ** (252 / max(n_days, 1)) - 1

        values = np.array(self._values)
        daily_returns = np.diff(values) / values[:-1] if len(values) > 1 else []

        return {
            "total_return": float(total_return),
            "annual_return": float(annual_return),
            "initial_value": self._initial,
            "final_value": final,
            "n_days": n_days,
            "daily_returns": daily_returns.tolist(),
        }
