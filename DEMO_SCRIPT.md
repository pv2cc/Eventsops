# EventOps — 5-Minute Judge Demo Script

**Theme:** Event-Driven Congestion (Planned & Unplanned)  
**System:** EventOps — forecast → optimise → prevent

---

## Opening (30 sec)

> "Bengaluru traffic breaks down around events — rallies, festivals, and sudden breakdowns. Today, impact isn't forecast in advance, deployment is experience-driven, and there's no learning loop. EventOps fixes that using the full incident lifecycle dataset — 8,173 real events, 54 police stations."

**Show:** Dashboard header metrics (total events, breakdown count, MAE, vehicle-hours avoided).

---

## Act 1 — Smart Dispatch (90 sec)

1. Open sidebar **Simulate new event**.
2. Set:
   - Event cause: **vehicle_breakdown**
   - Corridor: **Tumkur Road**
   - Priority: **High**
   - Hour: **17** (peak)
3. Click **Run Smart Dispatch**.

**Say:**

> "When a new breakdown is logged, EventOps instantly recommends which station should respond, predicts clearance time, and checks if that station is already overloaded."

**Point to panel:**
- Recommended station name
- Predicted clearance (~88 min) + confidence band
- **Reroute message** if top station was overloaded (e.g. Peenya → Jalahalli)

**Say:**

> "The ranking is transparent — distance, live load, and historical clearance speed — not a black box. Judges can ask why we picked this station and we can show the score breakdown."

---

## Act 2 — Breakdown Risk (90 sec)

1. Ensure **Breakdown risk layer** and **Pre-staged units** are checked on the map.

**Say:**

> "We don't just react faster — we prevent breakdown collapse. This corridor-time risk surface aggregates 4,896 historical breakdowns by corridor, hour, and day."

**Point to map:**
- Large red/orange corridor circles = high risk
- Heatmap = breakdown density
- Green markers = 5 pre-staged clearance units

**Say:**

> "Greedy pre-staging covers 48.5% of historical breakdown volume. Our headline metric: **1,779 vehicle-hours of closure avoided** per week versus purely reactive dispatch — assuming a 45-minute reactive delay before clearance starts."

---

## Act 3 — Full Loop (60 sec)

1. Expand **Recent events table** — show `live_load`, corridor, station.
2. Toggle event layers / status filter to show active vs closed.

**Say:**

> "Every closed event is a labelled training example. Clearance times, station load, corridor patterns — the model retrains as new events resolve. Same pipeline scales to any zone or corridor in the dataset."

---

## Honest Framing (if asked)

- We forecast **incident impact and resource need**, not km/h traffic speed — the dataset has no flow data.
- Truck age/cargo columns were only 3.4% filled, so breakdown risk uses **corridor × time × vehicle type** instead of truck-profile ML.
- `assigned_to_police_id` is sparse (1.6%), so dispatch uses **station centroids + live load**, not assignment timestamps.

---

## Close (30 sec)

> "EventOps delivers the complete loop on one screen: **forecast** clearance impact, **optimise** station deployment with load balancing, and **prevent** breakdown congestion through pre-staging. Built entirely on the provided dataset — feasible today, scalable tomorrow, learning every week."

---

## Quick launch

```bash
cd "c:\Users\verma\Downloads\Flipkart Gridlock Prototype"
streamlit run app.py
```

Retrain all models:

```bash
python run_train_all.py
```
