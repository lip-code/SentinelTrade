"""Streamlit dashboard main entry point.

Run with: streamlit run src/dashboard/app.py
"""
import streamlit as st
from src.database.engine import DatabaseEngine
from src.dashboard.pages.portfolio import render_portfolio_page
from src.dashboard.pages.signals import render_signals_page
from src.dashboard.pages.trades import render_trades_page
from src.dashboard.pages.risk import render_risk_page


def create_dashboard(db_path: str = "data/sentinel.db") -> None:
    st.set_page_config(page_title="SentinelTrade", layout="wide")
    st.title("SentinelTrade Dashboard")

    db_engine = DatabaseEngine(db_path)
    db_engine.init_tables()

    page = st.sidebar.selectbox("Navigation", ["Portfolio", "Signals", "Trades", "Risk"])

    if st.sidebar.button("Refresh"):
        st.rerun()

    if page == "Portfolio":
        render_portfolio_page(db_engine)
    elif page == "Signals":
        render_signals_page(db_engine)
    elif page == "Trades":
        render_trades_page(db_engine)
    elif page == "Risk":
        render_risk_page(db_engine)


if __name__ == "__main__":
    create_dashboard()
