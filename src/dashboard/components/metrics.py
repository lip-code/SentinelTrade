"""Metric card components for Streamlit dashboard."""
import streamlit as st


def render_account_metrics(
    total_assets: float,
    daily_pnl: float,
    position_count: int,
    max_drawdown: float,
) -> None:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Assets", f"{total_assets:,.2f}")
    col2.metric("Daily P&L", f"{daily_pnl:,.2f}", delta=f"{daily_pnl:+.2f}")
    col3.metric("Positions", str(position_count))
    col4.metric("Max Drawdown", f"{max_drawdown:.2%}")
