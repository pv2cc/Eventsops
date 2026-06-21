"""Reusable UI widgets."""

from __future__ import annotations

import streamlit as st


def render_load_gauge(station: str, current: int, median: int, overloaded: bool) -> None:
    st.markdown(f"**Load gauge — {station}**")
    cap = max(median * 2, current, 1)
    st.progress(min(current / cap, 1.0))
    status = "OVERLOADED" if overloaded else "Normal"
    emoji = "⚠️" if overloaded else "✓"
    st.caption(f"{emoji} {current} open events · median {median} · **{status}**")


def render_before_after(impact: dict) -> None:
    st.markdown("**Before / After — Reactive vs Preventive**")
    c1, c2, c3 = st.columns(3)
    reactive = impact["reactive"]
    preventive = impact["preventive"]

    with c1:
        st.metric("Reactive total", f"{reactive['total_min']:.0f} min")
        st.caption(f"Delay {reactive['response_delay_min']:.0f} + clearance {reactive['clearance_min']:.0f}")
    with c2:
        st.metric(
            "Preventive total",
            f"{preventive['total_min']:.0f} min",
            delta=f"-{impact['minutes_saved_per_incident']:.0f} min",
            delta_color="inverse",
        )
        st.caption("Pre-staged corridor" if preventive["pre_staged_corridor"] else "Partial coverage")
    with c3:
        st.metric("Officer-hrs saved / wk", f"{impact['officer_hours_saved_per_week']:.0f}")
        st.caption(f"{impact['vehicle_hours_avoided_per_week']:,.0f} veh-hrs avoided")
