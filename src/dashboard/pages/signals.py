"""Signal history page."""
import streamlit as st
import pandas as pd
from src.database.repository import SignalRepository


def render_signals_page(db_engine) -> None:
    st.header("Signal History")
    repo = SignalRepository(db_engine)
    signals = repo.get_signals(limit=100)
    if signals:
        df = pd.DataFrame(signals)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No signals recorded")
