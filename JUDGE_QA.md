# EventOps — Judge Q&A Defense Sheet

Use this live during Q&A or rehearse before recording your demo video.

---

## Data integrity

**Q: Is your dataset the official ASTraM export?**  
A: Yes — 8,173 rows, identical ID set to the hackathon CSV. A re-export may differ in row order (checksum changes) but not in content. Models were trained on the repo copy; no retrain needed.

**Q: How many clearance labels are “real”?**  
A: **6,699 total** training labels for `effective_clearance_time_min`:
- **2,723** (~38%) from actual `closed_datetime`
- **~3,976** imputed from `modified_datetime` when an event is closed/resolved but lacks a close stamp

We document this in `src/spine.py` → `add_effective_close()`. Labels are range-validated (0–720 min). The UI shows a **confidence band** on each prediction because imputed targets skew longer (median ~50 min close-stamp-only vs ~128 min with imputation).

**Q: Does imputation inflate your MAE?**  
A: It shifts the target distribution upward. We report MAE ~54 min honestly and pair it with confidence intervals — we don’t claim sub-30-min precision.

---

## Theme 2 completeness

**Q: You only handle breakdowns — where’s planned congestion (rallies, festivals)?**  
A: The dataset contains **467 planned events** processed by the **same pipeline**:
- **311** construction
- **84** public_event · **38** procession · **20** vip_movement
- **142** crowd/VIP/procession events alone, plus construction

EventOps forecasts clearance, ranks stations, and scores closure likelihood for **both planned and unplanned** causes — Theme 2’s “event-driven” half is covered on one engine.

**Q: Why not a separate rally module?**  
A: ASTraM logs all events with the same lifecycle fields (coords, corridor, station, priority, closure flags). One spine + one dispatch model generalises across causes; the demo can simulate any `event_cause` in the sidebar.

---

## Heavy vehicles & Module 6.2

**Q: Truck age and cargo are empty — how do you do heavy-vehicle risk?**  
A: Correct — `age_of_truck`, `cargo_material`, `reason_breakdown` are **~3.4% filled**. We did **not** build a truck-profile model on 278 rows.

Instead we use **`veh_type` — 100% populated on breakdowns** (4,896 events):
| Vehicle type | Share of breakdowns |
|--------------|--------------------:|
| **BMTC bus** | **~30%** (1,466) |
| Heavy vehicle | ~20% (965) |
| LCV | ~14% (678) |
| Truck | ~6% (276) |
| **Buses + heavy + LCV + truck combined** | **~81%** |

**Sound bite:** *“BMTC buses are the #1 source of breakdown-driven congestion in this dataset — and buses plus heavy vehicles are 81% of all breakdowns. That’s our heavy-vehicle differentiator on fully populated data, not dead truck-attribute columns.”*

Risk surface can be segmented by `veh_type` to recover Module 6.2’s intent on solid ground.

---

## Breakdown patterns & pre-staging

**Q: Why corridor × hour × day — is there signal?**  
A: Yes. Breakdowns **twin-peak**:
- **Evening:** 7–10pm (~35% of breakdowns)
- **Early morning:** 4–6am (~20%)
- **~55% combined** in those windows

Demo line: *“We pre-stage for the 8pm peak because half of breakdown volume clusters in six hours of the day.”*

**Q: Top corridors?**  
A: Among **named** corridors, top 5 hold **~57%** of tagged breakdowns. **Mysore Road #1** (565 events), then Bellary Road 1, Tumkur Road. Pre-staging greedy-placed **5 units** cover **48.5%** of all breakdown volume.

**Q: What about “Non-corridor” events (~34%)?**  
A: They lack a named corridor tag but still have coordinates and police station. **Smart Dispatch** handles them via station centroids + live load. **Pre-staging** intentionally targets concentrated named corridors where ROI is highest; off-corridor events get reactive optimisation, not preventive staging.

---

## Impact numbers

**Q: 1,779 vehicle-hours — per week?**  
A: **No — total over the ~5-month ASTraM record (~21.4 weeks).** That’s **~83 vehicle-hours/week** and **~29 officer-hours/week** (est.). We state both total and weekly rate to avoid inflating impact.

**Q: How did you compute avoided vehicle-hours?**  
A: Covered breakdown events × **45 min reactive delay** (assumption stated upfront) ÷ 60. Greedy pre-staging covers 2,372 of 4,894 breakdown events → 1,779 veh-hrs total. Before/after panel compares reactive vs preventive delay per simulated incident.

---

## Smart Dispatch

**Q: Why not use `assigned_to_police_id`?**  
A: Only **~1.6% filled**. We use **station centroids + live load** + transparent weighted ranking (speed 40%, load 35%, distance 25%) with **overload reroute**.

**Q: Is dispatch a black box?**  
A: No — top 3 stations shown with score breakdown. Judges can ask “why this station?” and we answer with distance, load vs median, and historical clearance speed.

---

## Mappls & feasibility

**Q: Why is the map blank?**  
A: Streamlit iframe limitation on some browsers. Sidebar → **Open Mappls map in new tab** — full Mappls JS SDK works there.

**Q: Do you claim real-time traffic speed?**  
A: **No.** ASTraM has incident lifecycle data, not flow sensors. We forecast **clearance time, closure likelihood, and resource need** — not km/h congestion.

---

## One-minute elevator close

> “EventOps runs on 8,173 real ASTraM events — breakdowns **and** 467 planned rallies/construction/VIP moves on one engine. BMTC buses alone are 30% of breakdown congestion. We forecast clearance with disclosed labels, dispatch transparently with overload rerouting, and pre-stage five units covering half of breakdown volume — **1,779 vehicle-hours saved over five months**, honestly stated. Built on Mappls, learning every close event.”
