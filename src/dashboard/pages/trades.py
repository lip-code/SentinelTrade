"""Trade history page."""
import streamlit as st
import pandas as pd
from src.database.repository import TradeRepository


def render_trades_page(db_engine) -> None:
    st.header("Trade History")
    repo = TradeRepository(db_engine)
    trades = repo.get_trades(limit=100)
    if trades:
        df = pd.DataFrame(trades)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No trades recorded")
