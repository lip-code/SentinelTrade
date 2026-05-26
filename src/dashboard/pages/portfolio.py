"""Portfolio overview page."""
import streamlit as st
import pandas as pd
from src.dashboard.components.metrics import render_account_metrics
from src.dashboard.components.charts import render_equity_curve, render_drawdown_chart
from src.database.repository import PnlRepository


def render_portfolio_page(db_engine) -> None:
    st.header("Portfolio Overview")

    pnl_repo = PnlRepository(db_engine)
    history = pnl_repo.get_pnl_history(limit=252)

    if history:
        latest = history[0]
        total_assets = latest.get("total_assets", 0.0)
        daily_pnl = latest.get("pnl", 0.0)
        max_drawdown = max(row.get("drawdown", 0.0) for row in history)
    else:
        total_assets = 0.0
        daily_pnl = 0.0
        max_drawdown = 0.0

    render_account_metrics(
        total_assets=total_assets,
        daily_pnl=daily_pnl,
        position_count=0,
        max_drawdown=max_drawdown,
    )

    if history:
        dates = [row["date"] for row in reversed(history)]
        values = [row["total_assets"] for row in reversed(history)]
        drawdowns = [row.get("drawdown", 0.0) for row in reversed(history)]

        st.subheader("Equity Curve")
        render_equity_curve(dates, values)

        st.subheader("Drawdown")
        render_drawdown_chart(dates, drawdowns)

    st.subheader("Recent P&L")
    if history:
        df = pd.DataFrame(history)
        df = df[["date", "total_assets", "pnl", "drawdown"]].copy()
        df.columns = ["Date", "Total Assets", "P&L", "Drawdown"]
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No P&L history recorded yet")
