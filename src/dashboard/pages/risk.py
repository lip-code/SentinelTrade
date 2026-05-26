"""Risk status page."""
import streamlit as st
import pandas as pd
from src.database.repository import RiskEventRepository


def render_risk_page(db_engine) -> None:
    st.header("Risk Status")

    repo = RiskEventRepository(db_engine)
    events = repo.get_events(limit=50)

    breaker_active = False
    if events:
        for ev in events[:10]:
            if "circuit_breaker" in (ev.get("event_type") or "").lower():
                breaker_active = True
                break

    col1, col2 = st.columns(2)
    col1.metric("Circuit Breaker", "Active" if breaker_active else "Normal")
    col2.metric("Recent Risk Events", str(len(events)))

    st.subheader("Risk Events")
    if events:
        df = pd.DataFrame(events)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No risk events")
