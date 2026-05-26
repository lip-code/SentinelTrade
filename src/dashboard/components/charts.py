"""Chart components for Streamlit dashboard."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots


def render_equity_curve(dates: list, values: list) -> None:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=values, mode="lines", name="Equity"))
    fig.update_layout(title="Equity Curve", xaxis_title="Date", yaxis_title="Value", height=400)
    st.plotly_chart(fig, use_container_width=True)


def render_kline_with_ma(df: pd.DataFrame, code: str) -> None:
    fig = go.Figure(data=[go.Candlestick(
        x=df.index if "date" not in df.columns else df["date"],
        open=df["open"],
        high=df["high"],
        low=df["low"],
        close=df["close"],
        name=code,
    )])
    if "ma5" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["ma5"], mode="lines", name="MA5"))
    if "ma20" in df.columns:
        fig.add_trace(go.Scatter(x=df.index, y=df["ma20"], mode="lines", name="MA20"))
    fig.update_layout(title=f"{code} K-Line", height=500, xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)


def render_drawdown_chart(dates: list, drawdowns: list) -> None:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=[-d for d in drawdowns],
        fill="tozeroy",
        mode="lines",
        name="Drawdown",
        line=dict(color="#d62728"),
    ))
    fig.update_layout(title="Drawdown", height=300)
    st.plotly_chart(fig, use_container_width=True)
