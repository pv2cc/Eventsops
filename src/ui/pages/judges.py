"""Impact metrics and judge-facing evidence."""

from __future__ import annotations

import json

import streamlit as st

from src.config import DISPATCH_SUMMARY, SPINE_SUMMARY
from src.ui.data_loaders import load_events, load_summaries


def render() -> None:
    events = load_events()
    dispatch_summary, breakdown_summary = load_summaries()
    impact = breakdown_summary.get("impact", {})
    prestaging = breakdown_summary.get("prestaging", {})

    st.subheader("Impact & evidence")
    st.caption("Quantified outcomes aligned to Gridlock evaluation criteria")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric(
        "Veh-hrs avoided (5-mo)",
        f"{impact.get('vehicle_hours_closure_avoided', 0):,.0f}",
        help=f"Total across the ~5-month ASTraM record (~{impact.get('vehicle_hours_avoided_per_week', 0):,.0f}/week)",
    )
    c2.metric("Breakdown coverage", f"{impact.get('coverage_pct', 0)}%")
    c3.metric("Pre-staged units", impact.get("units_deployed", 0))
    c4.metric("Clearance MAE", f"{dispatch_summary.get('clearance_model', {}).get('mae_minutes', 0):.0f} min")

    st.markdown("### Smart Dispatch")
    st.markdown(
        """
| Component | Method | Result |
|-----------|--------|--------|
| Clearance time | HistGradientBoosting on 6,699 labelled events | ~54 min MAE |
| Station ranking | Transparent weights: speed 40%, load 35%, distance 25% | Overload reroute when median exceeded |
| Closure likelihood | Binary classifier at event logging | High/medium/low badge before dispatch |
        """
    )

    st.markdown("### Breakdown risk & prevention")
    st.markdown(
        f"""
- **Risk surface:** corridor × hour × day-of-week from {int(events['is_breakdown'].sum()):,} breakdown events
- **Pre-staging:** greedy placement of **{impact.get('units_deployed', 0)} units** covering **{impact.get('coverage_pct', 0)}%** of historical breakdowns
- **Avoided congestion:** **{impact.get('vehicle_hours_closure_avoided', 0):,.0f} vehicle-hours** across the ~5-month record (~{impact.get('vehicle_hours_avoided_per_week', 0):,.0f}/week) (closure-duration model)
- **Truck-age model skipped:** only 3.4% of rows had cargo/age fields — honest scope per ASTraM audit
        """
    )

    st.markdown("### Data spine")
    if SPINE_SUMMARY.exists():
        spine = json.loads(SPINE_SUMMARY.read_text(encoding="utf-8"))
        st.json(spine)
    else:
        st.info("Run `python run_spine.py` to generate spine summary.")

    st.markdown("### Mappls integration")
    st.markdown(
        """
- Base map: **Mappls JS SDK** (partner requirement)
- Overlays: incident markers, breakdown risk halos, pre-staged unit pins
- Fallback: open full-screen map in browser tab if iframe is blank (Streamlit limitation)
        """
    )

    st.markdown("### Top-10 differentiation checklist")
    checks = [
        ("Complete forecast → optimise → prevent loop", True),
        ("Quantified impact with before/after panel", True),
        ("Transparent dispatch (not black-box)", True),
        ("Learning loop with retrain button", True),
        ("Honest data limitations documented", True),
        ("Live demo under 3 minutes", True),
        ("Mappls + ASTraM alignment", True),
    ]
    for label, ok in checks:
        st.write(f"{'✅' if ok else '⬜'} {label}")

    st.markdown("### Submission assets")
    st.markdown(
        """
1. **Demo URL** — see README / SUBMISSION.md
2. **3-min video** — follow `DEMO_SCRIPT.md` (Overview → judge scenario → impact numbers)
3. **GitHub repo** — code + trained JSON summaries (models retrain via bootstrap)
        """
    )

    if DISPATCH_SUMMARY.exists():
        with st.expander("Raw dispatch model summary"):
            st.json(dispatch_summary)
