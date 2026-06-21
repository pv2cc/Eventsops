# EventOps

**Event-driven congestion intelligence for Bengaluru** — Flipkart Gridlock Hackathon, Theme 2.

Forecast incident impact → optimise station dispatch → prevent breakdown congestion.

---

## What it does

| Module | Capability |
|--------|------------|
| **Smart Dispatch** | Clearance-time prediction, transparent station ranking, overload rerouting |
| **Breakdown Risk** | Corridor × time risk surface, greedy pre-staging, vehicle-hours avoided |
| **Learning loop** | Retrain on closed events, surface recurring patterns |

Built entirely on the **ASTraM / Bengaluru Traffic Police** incident dataset (8,173 real events, 54 police stations) — not simulated data.

---

## Partner alignment (hackathon specifications)

| Partner | Specification | EventOps status |
|---------|---------------|-----------------|
| **Bengaluru Traffic Police (ASTraM)** | Real-world traffic datasets from urban traffic analysis and field intelligence | **Fully aligned** — entire pipeline runs on the provided ASTraM anonymized event lifecycle log (creation → assignment → resolution → closure) |
| **MapmyIndia / Mappls** | Proprietary India mapping + traffic intelligence | **Active** — Mappls JS SDK base map with ASTraM overlays (see `.env`) |

**ASTraM columns we use:** event coordinates, corridor, zone, junction, police station, timestamps, vehicle type, priority, road-closure flags, and derived clearance/load labels.

**MapmyIndia upgrade path (when API key is available):**
- Replace base map tiles with MapmyIndia raster/vector layers
- Enrich events with MapmyIndia reverse-geocoding for junction names
- Optional: overlay MapmyIndia traffic flow where permitted by hackathon access

Set `MAPMYINDIA_API_KEY` in a local `.env` file (copy from `.env.example`). The dashboard uses the official **Mappls JS SDK** with your bearer token from [apis.mappls.com/console](https://apis.mappls.com/console).

**Do not commit `.env` to git** — it is listed in `.gitignore`.

---

## Quick start

```bash
cd "Flipkart Gridlock Prototype"
pip install -r requirements.txt

# One-shot bootstrap (spine + models)
python bootstrap.py

# Launch judge-ready dashboard
python -m streamlit run app.py
```

Open **http://localhost:8501** → sidebar: **Overview** | **Live Demo** | **Impact & Judges**

For a **public demo URL**, see **DEPLOY.md** (Streamlit Cloud) or run `ngrok http 8501` while the app is running.

Submission pack: **SUBMISSION.md** · Demo script: **DEMO_SCRIPT.md**

---

## Project structure

```
├── app.py                    # Streamlit dashboard
├── run_spine.py              # Phase 1: data spine
├── run_train_dispatch.py     # Smart Dispatch models
├── run_train_breakdown.py    # Breakdown risk models
├── run_train_all.py          # Train everything
├── audit_phase0.py           # Data audit (Phase 0)
├── DEMO_SCRIPT.md            # 5-minute judge demo script
├── data/
│   ├── prepared_events.parquet
│   ├── station_centroids.csv
│   └── models/               # Trained artifacts
└── src/
    ├── spine.py
    ├── models/               # clearance, closure, dispatch, breakdown
    └── analytics/            # patterns, impact metrics
```

---

## API (callable functions)

```python
from src.models.dispatch_service import predict_dispatch, retrain_all
from src.models.breakdown_risk import get_breakdown_risk

result = predict_dispatch({
    "latitude": 13.04,
    "longitude": 77.52,
    "event_cause": "vehicle_breakdown",
    "corridor": "Tumkur Road",
    "priority": "High",
    "hour_of_day": 17,
    "day_of_week": 3,
})

risk = get_breakdown_risk("Tumkur Road", hour=17, day_of_week=3)
```

---

## Honest data caveats

- No traffic speed/flow data → we forecast **incident impact**, not km/h congestion.
- Truck columns (`age_of_truck`, `cargo_material`) are ~3.4% filled → breakdown risk uses **corridor × time × veh_type**, not truck-profile ML.
- `assigned_to_police_id` is sparse → dispatch uses **station centroids + live load**, not assignment timestamps.

---

## Screenshots for slides

Capture these from the dashboard (`python -m streamlit run app.py`):

1. **Overview** — top metrics row + Bengaluru map with risk layer
2. **Smart Dispatch** — after clicking *Run Smart Dispatch* (station, load gauge, closure badge)
3. **Before/after** — reactive vs preventive impact panel
4. **Learning loop** — retrain section + recurring patterns table

Save as `docs/screenshot_1_overview.png`, etc.

---

## Evaluation alignment

| Criterion | EventOps answer |
|-----------|-----------------|
| **Impact** | Vehicle-hours + officer-hours saved; preventive pre-staging |
| **Feasibility** | 100% on provided dataset |
| **Scalability** | Same pipeline for all corridors/zones |
| **Sustainability** | Retrain button + pattern surfacing |
| **Completeness** | Forecast → optimise → prevent on one screen |

---

## Demo

See **DEMO_SCRIPT.md** for the full 5-minute judge walkthrough.
