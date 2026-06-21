# EventOps — Flipkart Gridlock Submission Pack

**Theme:** 2 — Event-Driven Congestion  
**Team product:** EventOps — forecast → optimise → prevent  
**Data:** ASTraM anonymized lifecycle events (8,173 rows, 54 stations, Nov 2023–Apr 2024)  
**Maps:** Mappls (MapmyIndia) JS SDK  

---

## Demo URL

| Environment | URL |
|-------------|-----|
| **Public demo (live)** | **https://2e29-2405-201-6812-835-180a-c257-c07d-48bc.ngrok-free.app** |
| **Local** | http://localhost:8505 (while ngrok tunnel is running) |
| **Permanent (Streamlit Cloud)** | Deploy using `DEPLOY.md` — replace ngrok URL before final submission |

> **For judges:** Open **Live Demo** → click **Run judge demo scenario** → watch dispatch + impact panel update in under 60 seconds.

---

## One-line pitch

EventOps turns every ASTraM incident into a **clearance forecast**, a **transparent station dispatch**, and a **preventive breakdown pre-staging plan** — closing the loop as new events resolve.

---

## Problem (Theme 2)

Bengaluru traffic police respond to thousands of unplanned events (breakdowns, accidents, protests). Today:

- Clearance time is guessed, not forecast at logging
- Dispatch follows habit, not live station load + distance
- Breakdown hotspots repeat weekly with no preventive staging
- Resolved events are not fed back into models

---

## Solution architecture

```
ASTraM CSV → Shared spine (parquet) → Models → Streamlit + Mappls dashboard
                      ↑                                    |
                      └──────── retrain on close ──────────┘
```

### Module A — Smart Dispatch
- **Clearance predictor:** HistGradientBoosting, MAE ~54 min on `effective_clearance_time_min`
- **Station recommender:** Weighted score (speed 40%, load 35%, distance 25%) + overload reroute
- **Closure predictor:** High/medium/low badge at event creation

### Module B — Breakdown risk
- Corridor × hour × day risk surface (honest substitute — truck-age fields 96.6% empty)
- Greedy pre-staging: **5 units**, **48.5% coverage**, **~1,779 veh-hrs avoided over the 5-month record (~83/wk)**

---

## Quantified impact (from trained models)

| Metric | Value |
|--------|-------|
| Historical events | 8,173 |
| Labelled clearance times | 6,699 |
| Clearance model MAE | ~54 min |
| Pre-staged units | 5 |
| Breakdown coverage | 48.5% |
| Vehicle-hours avoided (5-mo record) | ~1,779 (≈83/wk) |
| Officer-hours saved (5-mo record, est.) | ~623 (≈29/wk) |

---

## Honest limitations (judges appreciate this)

- No km/h or live traffic volume — not in ASTraM dataset
- `assigned_to_police_id` sparse (1.6%) — dispatch uses station centroids + synthetic live load
- Truck age / cargo / breakdown reason model **not built** — fields 96.6% missing (Phase 0 audit)

---

## Evaluation criteria mapping

| Criterion | How EventOps scores |
|-----------|---------------------|
| **Impact** | 1,779 veh-hrs avoided over 5-mo record (~83/wk) + before/after panel per simulated incident |
| **Feasibility** | 100% on provided CSV; no external traffic APIs required |
| **Scalability** | Same pipeline for all corridors and 54 stations |
| **Sustainability** | Retrain button + pattern tab; each close event is a label |
| **Completeness** | Full loop on one dashboard; Mappls map + dispatch + prevention |
| **Innovation** | Transparent ranking + overload reroute + preventive pre-staging |

---

## How to run locally

```bash
pip install -r requirements.txt
python bootstrap.py          # first run only (~1–2 min)
python -m streamlit run app.py
```

Add `.env`:
```
MAPMYINDIA_API_KEY=your_map_sdk_key
```

---

## 3-minute demo script

See `DEMO_SCRIPT.md`:

1. **Overview** (30s) — problem, loop, metrics
2. **Live Demo** (90s) — judge scenario → dispatch → before/after
3. **Impact & Judges** (60s) — numbers + differentiation checklist

---

## Top 10 strategy (out of ~1,600 teams)

### What separates finalists

1. **Show the loop, not a slide** — live dispatch beats static architecture diagrams
2. **One killer number** — lead with **1,779 veh-hrs of closure avoided** across the 5-month record (~83/wk)
3. **Transparency** — explain dispatch weights; judges distrust black boxes
4. **Honesty** — call out sparse fields; shows you read the data
5. **Partner alignment** — Mappls map visible; ASTraM columns named in UI
6. **Video quality** — 1080p screen recording, mic clear, under 3 minutes
7. **Repo hygiene** — README + SUBMISSION + one-command bootstrap

### Submission checklist

- [ ] Public demo URL (Streamlit Cloud or ngrok HTTPS)
- [ ] GitHub repo link (exclude `.env`)
- [ ] 3-min demo video
- [ ] Problem statement + impact table (copy from this doc)
- [ ] Map screenshot with risk layer + pre-staged units
- [ ] Mention Theme 2 explicitly in title slide

### Avoid

- Claiming real-time km/h traffic
- Theme 1 parking or Theme 3 CV features
- Folium/Leaflet when Mappls is partner stack
- Empty map in video — use **Open Mappls map in new tab** if iframe blank

---

## Files judges should open

| File | Purpose |
|------|---------|
| `app.py` | Main dashboard |
| `src/spine.py` | Data preparation |
| `src/models/dispatch_service.py` | End-to-end dispatch API |
| `src/models/breakdown_risk.py` | Risk + pre-staging |
| `data/models/dispatch_summary.json` | Model metrics |
| `DEMO_SCRIPT.md` | Recorded demo flow |

---

## Contact / attribution

Built for Flipkart Gridlock Hackathon · Theme 2 · Bengaluru Traffic Police ASTraM data · Mappls maps
