"""
Plotting utilities for backtest results.

Uses Plotly for interactive charts. Supports:
- Equity curve
- Drawdown curve
- Trade distribution
- K-line with moving averages
- Optimization results heatmap
"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from src.backtest.performance import PerformanceReport


def plot_equity_curve(report: PerformanceReport, title: str = "Equity Curve") -> go.Figure:
    """Plot equity curve with drawdown overlay."""
    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(title, "Drawdown"),
    )

    fig.add_trace(
        go.Scatter(
            y=report.equity_curve,
            mode="lines",
            name="Equity",
            line=dict(color="#1f77b4", width=1.5),
        ),
        row=1,
        col=1,
    )

    fig.add_trace(
        go.Scatter(
            y=[-d for d in report.drawdown_curve],
            fill="tozeroy",
            mode="lines",
            name="Drawdown",
            line=dict(color="#d62728", width=1),
            fillcolor="rgba(214, 39, 40, 0.3)",
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        height=600,
        showlegend=True,
        template="plotly_white",
        yaxis_title="Value (¥)",
        yaxis2_title="Drawdown",
    )

    return fig


def plot_trade_distribution(report: PerformanceReport, title: str = "Trade P&L Distribution") -> go.Figure:
    """Plot histogram of trade P&L values."""
    if not report.trade_log:
        fig = go.Figure()
        fig.add_annotation(text="No trades to display", showarrow=False)
        return fig

    pnls = [t["pnl"] for t in report.trade_log]
    colors = ["#2ca02c" if p > 0 else "#d62728" for p in pnls]

    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=pnls,
        nbinsx=30,
        marker_color=colors,
        name="P&L",
    ))

    fig.update_layout(
        title=title,
        xaxis_title="P&L (¥)",
        yaxis_title="Count",
        template="plotly_white",
        height=400,
    )

    return fig


def plot_monthly_returns(report: PerformanceReport, title: str = "Monthly Returns") -> go.Figure:
    """Plot monthly returns heatmap."""
    if not report.equity_curve or len(report.equity_curve) < 2:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient data for monthly returns", showarrow=False)
        return fig

    values = np.array(report.equity_curve)
    daily_returns = np.diff(values) / values[:-1]

    n = len(daily_returns)
    months = min(n // 21, 12)
    if months < 1:
        fig = go.Figure()
        fig.add_annotation(text="Insufficient data for monthly returns", showarrow=False)
        return fig

    monthly = []
    for i in range(months):
        start = i * 21
        end = min(start + 21, n)
        month_return = np.sum(daily_returns[start:end])
        monthly.append(month_return)

    fig = go.Figure(data=go.Bar(
        x=[f"M{i+1}" for i in range(len(monthly))],
        y=monthly,
        marker_color=["#2ca02c" if r > 0 else "#d62728" for r in monthly],
    ))

    fig.update_layout(
        title=title,
        xaxis_title="Month",
        yaxis_title="Return",
        template="plotly_white",
        height=350,
    )

    return fig


def plot_kline_with_ma(
    df: pd.DataFrame,
    code: str,
    ma_periods: list[int] | None = None,
    title: str | None = None,
) -> go.Figure:
    """Plot K-line chart with moving averages."""
    if ma_periods is None:
        ma_periods = [5, 10, 20]

    fig = make_subplots(
        rows=2,
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.03,
        row_heights=[0.7, 0.3],
        subplot_titles=(title or f"{code} K-Line", "Volume"),
    )

    fig.add_trace(
        go.Candlestick(
            x=df.index if "date" not in df.columns else df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=code,
        ),
        row=1,
        col=1,
    )

    colors = ["#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]
    for i, period in enumerate(ma_periods):
        ma = df["close"].rolling(window=period).mean()
        fig.add_trace(
            go.Scatter(
                x=df.index if "date" not in df.columns else df["date"],
                y=ma,
                mode="lines",
                name=f"MA{period}",
                line=dict(color=colors[i % len(colors)], width=1),
            ),
            row=1,
            col=1,
        )

    volume_colors = ["#2ca02c" if c >= o else "#d62728" for c, o in zip(df["close"], df["open"])]
    fig.add_trace(
        go.Bar(
            x=df.index if "date" not in df.columns else df["date"],
            y=df["volume"],
            marker_color=volume_colors,
            name="Volume",
            showlegend=False,
        ),
        row=2,
        col=1,
    )

    fig.update_layout(
        height=600,
        xaxis_rangeslider_visible=False,
        template="plotly_white",
    )

    return fig


def plot_optimization_results(
    results: list[dict[str, Any]],
    x_param: str,
    y_param: str,
    color_metric: str = "sharpe",
    title: str = "Optimization Results",
) -> go.Figure:
    """Plot optimization results as scatter plot."""
    if not results:
        fig = go.Figure()
        fig.add_annotation(text="No optimization results", showarrow=False)
        return fig

    x_vals = [r["params"].get(x_param, 0) for r in results]
    y_vals = [r["params"].get(y_param, 0) for r in results]
    colors = [r.get(color_metric, 0) for r in results]

    fig = go.Figure(data=go.Scatter(
        x=x_vals,
        y=y_vals,
        mode="markers",
        marker=dict(
            size=10,
            color=colors,
            colorscale="RdYlGn",
            showscale=True,
            colorbar=dict(title=color_metric),
        ),
        text=[f"Sharpe: {r.get('sharpe', 0):.2f}<br>Return: {r.get('total_return', 0):.2%}" for r in results],
        hoverinfo="text",
    ))

    fig.update_layout(
        title=title,
        xaxis_title=x_param,
        yaxis_title=y_param,
        template="plotly_white",
        height=500,
    )

    return fig


def generate_html_report(report: PerformanceReport, output_path: str = "backtest_report.html") -> None:
    """Generate a standalone HTML report with all charts."""
    equity_fig = plot_equity_curve(report)
    trade_fig = plot_trade_distribution(report)
    monthly_fig = plot_monthly_returns(report)

    html_parts = [
        "<html><head><title>SentinelTrade Backtest Report</title>",
        "<script src='https://cdn.plot.ly/plotly-latest.min.js'></script>",
        "<style>body{font-family:Arial;margin:20px} .chart{margin:20px 0} pre{background:#f5f5f5;padding:15px;border-radius:5px}</style>",
        "</head><body>",
        "<h1>SentinelTrade Backtest Report</h1>",
        f"<pre>{report.summary()}</pre>",
        "<div class='chart'>" + equity_fig.to_html(full_html=False) + "</div>",
        "<div class='chart'>" + trade_fig.to_html(full_html=False) + "</div>",
        "<div class='chart'>" + monthly_fig.to_html(full_html=False) + "</div>",
        "</body></html>",
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))
