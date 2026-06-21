"""Overview / pitch page for judges."""

from __future__ import annotations

import streamlit as st


def render(impact: dict, dispatch_summary: dict, event_count: int, breakdown_count: int) -> None:
    st.markdown(
        """
<div class="hero">
  <h1>EventOps</h1>
  <p>Event-driven congestion intelligence for Bengaluru · Theme 2 · Flipkart Gridlock</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        '<div class="badge-row">'
        '<span>ASTraM Data</span><span>Mappls Maps</span>'
        '<span>Smart Dispatch</span><span>Breakdown Risk</span>'
        '<span>Closed-loop Learning</span></div>',
        unsafe_allow_html=True,
    )

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Historical events", f"{event_count:,}")
    c2.metric("Breakdown incidents", f"{breakdown_count:,}")
    c3.metric("Clearance model MAE", f"{dispatch_summary.get('clearance_model', {}).get('mae_minutes', 0):.0f} min")
    c4.metric(
        "Veh-hrs avoided (5-mo)",
        f"{impact.get('vehicle_hours_closure_avoided', 0):,.0f}",
        help=f"Total across the ~5-month record (~{impact.get('vehicle_hours_avoided_per_week', 0):,.0f}/week)",
    )

    st.subheader("Problem → Solution")
    p1, p2 = st.columns(2)
    with p1:
        st.markdown(
            """
**Theme 2 pain points**
- Event impact not quantified in advance
- Resource deployment is experience-driven
- No post-event learning loop
            """
        )
    with p2:
        st.markdown(
            """
**EventOps loop (forecast → optimise → prevent)**
1. **Forecast** clearance time + closure likelihood at logging
2. **Optimise** transparent station dispatch with overload rerouting
3. **Prevent** breakdown congestion via corridor-time pre-staging
            """
        )

    st.subheader("Architecture")
    st.markdown(
        """
```mermaid
flowchart LR
  A[ASTraM Incident Log] --> B[Shared Data Spine]
  B --> C[Smart Dispatch]
  B --> D[Breakdown Risk]
  C --> E[Mappls Dashboard]
  D --> E
  E --> F[Learning Loop Retrain]
  F --> B
```
        """
    )

    st.subheader("Evaluation alignment")
    rows = [
        ("Impact", "1,779 veh-hrs avoided over 5-mo record (~83/wk) · officer-hours saved · preventive breakdown clearance"),
        ("Feasibility", "100% built on provided ASTraM dataset — 8,173 real lifecycle events"),
        ("Scalability", "Same pipeline for all corridors, zones, and 54 police stations"),
        ("Sustainability", "Retrain on every closed event · recurring pattern surfacing"),
        ("Completeness", "End-to-end loop on one screen — live demo in next tab"),
    ]
    for criterion, proof in rows:
        st.markdown(f"**{criterion}** — {proof}")

    with st.expander("Honest data framing (what we do NOT claim)"):
        st.markdown(
            """
- No km/h traffic-flow claims — dataset has no speed/volume sensors
- Truck age/cargo model skipped (3.4% fill) — corridor × time risk used instead
- Dispatch uses station centroids + live load, not sparse assignment timestamps
            """
        )

    st.info("Go to **Live Demo** in the sidebar and click **Run judge demo scenario**.")
