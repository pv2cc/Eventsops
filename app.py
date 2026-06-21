"""EventOps — Flipkart Gridlock Theme 2 prototype."""

from __future__ import annotations

import streamlit as st

from bootstrap import ensure_artifacts
from src.ui.data_loaders import load_events, load_summaries
from src.ui.pages import demo, judges, overview
from src.ui.styles import CUSTOM_CSS

st.set_page_config(
    page_title="EventOps | Flipkart Gridlock",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = {
    "Overview": overview.render,
    "Live Demo": demo.render,
    "Impact & Judges": judges.render,
}


@st.cache_resource
def _bootstrap_once() -> bool:
    with st.spinner("Preparing ASTraM data spine and models (first run only)…"):
        ensure_artifacts()
    return True


def main() -> None:
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    _bootstrap_once()

    events = load_events()
    dispatch_summary, breakdown_summary = load_summaries()
    impact = breakdown_summary.get("impact", {})

    st.sidebar.title("EventOps")
    st.sidebar.caption("Theme 2 · Event-Driven Congestion · Bengaluru")

    choice = st.sidebar.radio("Navigate", list(PAGES.keys()), label_visibility="collapsed")

    st.sidebar.divider()
    st.sidebar.metric("Events", f"{len(events):,}")
    st.sidebar.metric(
        "Veh-hrs avoided",
        f"{impact.get('vehicle_hours_closure_avoided', 0):,.0f}",
        help=f"Total across the ~5-month record (~{impact.get('vehicle_hours_avoided_per_week', 0):,.0f}/week)",
    )

    page_fn = PAGES[choice]
    if choice == "Overview":
        page_fn(
            impact,
            dispatch_summary,
            len(events),
            int(events["is_breakdown"].sum()),
        )
    else:
        page_fn()


if __name__ == "__main__":
    main()
