"""Shared map layer builders for Mappls."""

from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components

from src.config import MAPMYINDIA_API_KEY, MAPPLS_MAP_HTML, PRESTAGING_PLAN
from src.dashboard.mappls_view import build_mappls_html, save_mappls_page
from src.models.breakdown_risk import get_corridor_heatmap, load_prestaging

RISK_COLORS = {"high": "#d32f2f", "medium": "#f57c00", "low": "#388e3c"}


def risk_color(score: float, max_score: float) -> str:
    ratio = score / max(max_score, 1.0)
    if ratio >= 0.6:
        return RISK_COLORS["high"]
    if ratio >= 0.3:
        return RISK_COLORS["medium"]
    return RISK_COLORS["low"]


def collect_map_layers(events, show_events, show_risk, show_prestage, event_limit):
    markers, circles = [], []

    if show_risk:
        heat_df = get_corridor_heatmap()
        max_risk = float(heat_df["total_risk"].max())
        for _, row in heat_df.iterrows():
            corridor_events = events[events["corridor_filled"] == row["corridor_filled"]]
            if corridor_events.empty:
                continue
            circles.append(
                {
                    "lat": float(corridor_events["latitude"].mean()),
                    "lng": float(corridor_events["longitude"].mean()),
                    "radius": 600 + min(row["total_risk"] / max_risk, 1) * 1400,
                    "color": risk_color(row["total_risk"], max_risk),
                    "popup": (
                        f"<b>{row['corridor_filled']}</b><br>"
                        f"Risk: {row['total_risk']:.0f}<br>"
                        f"Breakdowns: {int(row['event_count'])}"
                    ),
                }
            )

    if show_prestage and PRESTAGING_PLAN.exists():
        for unit in load_prestaging().get("placements", []):
            markers.append(
                {
                    "lat": unit["latitude"],
                    "lng": unit["longitude"],
                    "popup": f"<b>Unit {unit['unit_id']}</b> · {unit['corridor']} · {unit['covered_events']} events",
                }
            )

    if show_events:
        for _, row in events.sort_values("created_date", ascending=False).head(event_limit).iterrows():
            markers.append(
                {
                    "lat": float(row["latitude"]),
                    "lng": float(row["longitude"]),
                    "popup": (
                        f"<b>{row['event_cause']}</b> ({row['priority']})<br>"
                        f"{row['corridor_filled']} · {row['police_station']}"
                    ),
                }
            )

    return markers, circles


def render_mappls_map(events, show_events, show_risk, show_prestage, event_limit, height: int = 560):
    if not MAPMYINDIA_API_KEY:
        st.error("Mappls API key missing. Add `MAPMYINDIA_API_KEY` to `.env` or Streamlit secrets.")
        return

    markers, circles = collect_map_layers(
        events, show_events, show_risk, show_prestage, min(event_limit, 150)
    )
    html_doc = build_mappls_html(MAPMYINDIA_API_KEY, markers, circles, height=height)
    save_mappls_page(html_doc, MAPPLS_MAP_HTML)
    components.html(html_doc, height=height + 20, scrolling=False)
    st.caption("© Mappls (MapmyIndia) · ASTraM lifecycle data overlays")
