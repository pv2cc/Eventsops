"""Live demo — map, dispatch simulation, learning loop."""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone

import pandas as pd
import streamlit as st

from src.analytics.impact import compute_before_after, overload_manpower_note
from src.analytics.patterns import peak_windows_for_corridor, recurring_patterns
from src.config import MAPMYINDIA_API_KEY, MAPPLS_MAP_HTML, PRESTAGING_PLAN
from src.dashboard.mappls_view import build_mappls_html, save_mappls_page
from src.models.breakdown_risk import get_breakdown_risk, load_prestaging
from src.models.dispatch_service import load_retrain_history, predict_dispatch, retrain_all
from src.ui.components import render_before_after, render_load_gauge
from src.ui.data_loaders import load_events, load_summaries
from src.ui.map_utils import collect_map_layers, render_mappls_map

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
CLOSURE_BADGE = {"high": "🔴", "medium": "🟠", "low": "🟢"}


def _default_judge_scenario(events: pd.DataFrame) -> dict:
    breakdowns = events[events["is_breakdown"] == 1]
    if breakdowns.empty:
        breakdowns = events
    top = (
        breakdowns.groupby("corridor_filled")
        .size()
        .sort_values(ascending=False)
        .head(1)
        .index[0]
    )
    corridor_rows = events[events["corridor_filled"] == top]
    peak_hour = int(corridor_rows["hour_of_day"].mode().iloc[0])
    peak_dow = int(corridor_rows["day_of_week"].mode().iloc[0])
    return {
        "cause": "vehicle_breakdown",
        "corridor": top,
        "priority": "High",
        "veh_type": corridor_rows["veh_type_filled"].mode().iloc[0],
        "hour": peak_hour,
        "dow": peak_dow,
    }


def render() -> None:
    events = load_events()
    dispatch_summary, breakdown_summary = load_summaries()
    impact = breakdown_summary.get("impact", {})
    prestaging = load_prestaging() if PRESTAGING_PLAN.exists() else {"placements": [], "impact": {}}

    st.subheader("Live operations demo")
    st.caption("Forecast → optimise → prevent on one screen · Mappls + ASTraM")

    if "demo_scenario" not in st.session_state:
        st.session_state["demo_scenario"] = _default_judge_scenario(events)

    sidebar = st.sidebar
    sidebar.header("Demo controls")

    if sidebar.button("Run judge demo scenario", type="primary"):
        st.session_state["demo_scenario"] = _default_judge_scenario(events)
        st.session_state["auto_dispatch"] = True

    sidebar.header("Map layers")
    show_events = sidebar.checkbox("Live events", value=True)
    show_risk = sidebar.checkbox("Breakdown risk layer", value=True)
    show_prestage = sidebar.checkbox("Pre-staged units", value=True)
    event_limit = sidebar.slider("Events on map", 50, 500, 200, 50)
    status_filter = sidebar.multiselect(
        "Status filter",
        options=sorted(events["status"].unique()),
        default=["active", "resolved"],
    )

    if MAPMYINDIA_API_KEY and sidebar.button("Open Mappls map in new tab"):
        layers = collect_map_layers(
            events, show_events, show_risk, show_prestage, min(event_limit, 150)
        )
        save_mappls_page(build_mappls_html(MAPMYINDIA_API_KEY, *layers, height="100vh"), MAPPLS_MAP_HTML)
        subprocess.Popen(
            ["cmd", "/c", "start", "", str(MAPPLS_MAP_HTML.resolve())],
            shell=False,
        )

    scenario = st.session_state["demo_scenario"]
    corridors = sorted(events["corridor_filled"].unique())
    causes = sorted(events["event_cause"].unique())
    veh_types = sorted(events["veh_type_filled"].unique())

    sidebar.header("Simulate new event")
    def _idx(options, value, default=0):
        try:
            return options.index(value)
        except ValueError:
            return default

    sim_cause = sidebar.selectbox("Event cause", causes, index=_idx(causes, scenario["cause"]))
    sim_corridor = sidebar.selectbox("Corridor", corridors, index=_idx(corridors, scenario["corridor"]))
    sim_priority = sidebar.selectbox("Priority", ["High", "Low"], index=0 if scenario["priority"] == "High" else 1)
    sim_veh = sidebar.selectbox("Vehicle type", veh_types, index=_idx(veh_types, scenario["veh_type"]))
    sim_hour = sidebar.slider("Hour of day", 0, 23, scenario["hour"])
    sim_dow = sidebar.selectbox("Day", list(range(7)), index=scenario["dow"], format_func=lambda x: DAY_NAMES[x])

    peaks = peak_windows_for_corridor(sim_corridor, events)
    if peaks:
        sidebar.caption("Peak breakdown windows (historical)")
        for p in peaks[:3]:
            sidebar.write(f"· {p['day']} {p['hour']:02d}:00 — {p['events']} events")

    corridor_coords = events[events["corridor_filled"] == sim_corridor]
    sim_lat = float(corridor_coords["latitude"].mean())
    sim_lon = float(corridor_coords["longitude"].mean())

    run_dispatch = sidebar.button("Run Smart Dispatch", type="primary") or st.session_state.pop(
        "auto_dispatch", False
    )

    sidebar.divider()
    sidebar.header("Learning loop")
    if sidebar.button("Retrain models on latest data"):
        with st.spinner("Retraining models..."):
            retrain_result = retrain_all(events)
        load_events.clear()
        load_summaries.clear()
        st.sidebar.success("Retrain complete!")
        st.session_state["last_retrain"] = retrain_result

    history = load_retrain_history()
    if history:
        last = history[-1]
        sidebar.caption(
            f"Last retrain MAE: {last['before'].get('clearance_mae', '—')} → "
            f"{last['after'].get('clearance_mae', '—')} min"
        )

    tab_ops, tab_learn = st.tabs(["Operations", "Learning & patterns"])

    with tab_ops:
        left, right = st.columns([1.4, 1])

        with left:
            st.markdown("**Bengaluru operations map**")
            filtered = events[events["status"].isin(status_filter)] if status_filter else events
            render_mappls_map(filtered, show_events, show_risk, show_prestage, event_limit)

        with right:
            st.markdown("**Dispatch & risk panel**")

            if run_dispatch:
                now = datetime.now(timezone.utc).isoformat()
                event_payload = {
                    "latitude": sim_lat,
                    "longitude": sim_lon,
                    "event_type": "unplanned",
                    "event_cause": sim_cause,
                    "priority": sim_priority,
                    "corridor": sim_corridor,
                    "veh_type": sim_veh,
                    "requires_road_closure": False,
                    "hour_of_day": sim_hour,
                    "day_of_week": sim_dow,
                    "is_weekend": int(sim_dow in (5, 6)),
                    "created_date": now,
                }
                result = predict_dispatch(event_payload)
                risk = get_breakdown_risk(sim_corridor, hour=sim_hour, day_of_week=sim_dow)

                dispatch = result["dispatch"]
                clearance = result["clearance_prediction"]
                closure = result["closure_prediction"]
                recommended = dispatch["top_candidates"][0]
                if dispatch["recommended_station"] != recommended["police_station"]:
                    for cand in dispatch["top_candidates"]:
                        if cand["police_station"] == dispatch["recommended_station"]:
                            recommended = cand
                            break

                b = recommended["score_breakdown"]
                st.success(f"Recommended: **{dispatch['recommended_station']}**")
                if dispatch["rerouted_from_overload"]:
                    st.warning(dispatch["reroute_reason"])

                badge = CLOSURE_BADGE.get(closure["closure_likelihood"], "🟢")
                st.info(
                    f"{badge} **Road closure likelihood: {closure['closure_likelihood'].upper()}** "
                    f"({closure['closure_probability']}% probability)"
                )

                render_load_gauge(
                    dispatch["recommended_station"],
                    b["live_load"],
                    b["station_median_load"],
                    recommended["is_overloaded"],
                )
                st.caption(overload_manpower_note(dispatch["rerouted_from_overload"]))

                m1, m2, m3 = st.columns(3)
                m1.metric("Predicted clearance", f"{clearance['predicted_clearance_min']:.0f} min")
                m2.metric(
                    "Confidence",
                    f"{clearance['confidence_low_min']:.0f}–{clearance['confidence_high_min']:.0f} min",
                )
                m3.metric("Breakdown risk", risk["risk_level"].upper())

                render_before_after(
                    compute_before_after(
                        clearance["predicted_clearance_min"],
                        impact,
                        sim_corridor,
                        prestaging,
                    )
                )

                st.markdown("**Transparent ranking (top 3)**")
                for cand in dispatch["top_candidates"][:3]:
                    cb = cand["score_breakdown"]
                    overload = " ⚠️" if cand["is_overloaded"] else ""
                    st.write(
                        f"- **{cand['police_station']}** — {cand['total_score']:.2f}{overload}  \n"
                        f"  {cb['distance_km']} km · load {cb['live_load']}/{cb['station_median_load']}"
                    )
            else:
                st.info("Click **Run judge demo scenario** or **Run Smart Dispatch** in the sidebar.")

            st.divider()
            st.markdown("**Pre-staging plan**")
            if PRESTAGING_PLAN.exists():
                st.write(
                    f"**{impact.get('units_deployed', 0)} units** · "
                    f"**{impact.get('coverage_pct', 0)}%** breakdown coverage"
                )
                for unit in prestaging.get("placements", [])[:5]:
                    st.write(
                        f"- Unit {unit['unit_id']} → **{unit['corridor']}** "
                        f"({unit['covered_events']} events)"
                    )
            else:
                st.warning("Run `python bootstrap.py` to generate models.")

    with tab_learn:
        st.markdown("**Closed-loop learning**")
        st.write("Every resolved event is a labelled example. Retraining refreshes all models.")

        if "last_retrain" in st.session_state:
            lr = st.session_state["last_retrain"]
            c1, c2, c3 = st.columns(3)
            c1.metric(
                "Clearance MAE",
                f"{lr['after']['clearance_mae']:.1f} min",
                delta=f"{(lr['after']['clearance_mae'] or 0) - (lr['before'].get('clearance_mae') or 0):+.1f}",
                delta_color="inverse",
            )
            c2.metric("Closure AUC", f"{lr['after']['closure_auc']:.3f}")
            c3.metric("Breakdown coverage", f"{lr['after']['breakdown_coverage']}%")

        if history:
            st.markdown("**Retrain history**")
            st.dataframe(
                pd.DataFrame(
                    [
                        {
                            "time": h["timestamp"][:19],
                            "mae_before": h["before"].get("clearance_mae"),
                            "mae_after": h["after"].get("clearance_mae"),
                            "rows": h["rows_used"],
                        }
                        for h in history[-5:]
                    ]
                ),
                hide_index=True,
                use_container_width=True,
            )

        st.markdown("**Recurring patterns**")
        st.dataframe(recurring_patterns(events), hide_index=True, use_container_width=True)

    with st.expander("Recent events"):
        st.dataframe(
            events.sort_values("created_date", ascending=False)[
                [
                    "id",
                    "event_cause",
                    "corridor_filled",
                    "police_station",
                    "priority",
                    "status",
                    "hour_of_day",
                    "live_load",
                ]
            ].head(100),
            hide_index=True,
            use_container_width=True,
        )
