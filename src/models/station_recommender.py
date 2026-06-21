"""Transparent station ranking and overload-aware dispatch (Modules 5.2 + 5.3)."""

from __future__ import annotations

from datetime import datetime, timezone

import numpy as np
import pandas as pd

from src.config import PREPARED_EVENTS, STATION_CENTROIDS, STATION_STATS
from src.spine import haversine_km

WEIGHTS = {"speed": 0.40, "load": 0.35, "distance": 0.25}


def build_station_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Historical clearance speed lookup table per station / cause / corridor."""
    speed = (
        df.dropna(subset=["effective_clearance_time_min"])
        .groupby(["police_station", "event_cause", "corridor_filled"], as_index=False)
        .agg(
            hist_clearance_min=("effective_clearance_time_min", "median"),
            hist_event_count=("id", "count"),
        )
    )
    STATION_STATS.parent.mkdir(parents=True, exist_ok=True)
    speed.to_parquet(STATION_STATS, index=False)
    return speed


def load_station_stats() -> tuple[pd.DataFrame, pd.DataFrame]:
    centroids = pd.read_csv(STATION_CENTROIDS)
    speed = pd.read_parquet(STATION_STATS)
    load_stats = (
        pd.read_parquet(PREPARED_EVENTS)
        .groupby("police_station", as_index=False)
        .agg(station_median_load=("live_load", "median"))
    )
    stats = centroids.merge(load_stats, on="police_station", how="left")
    return stats, speed


def _lookup_clearance(
    station: str,
    event_cause: str,
    corridor: str,
    speed_table: pd.DataFrame,
    fallback_min: float,
) -> float:
    match = speed_table[
        (speed_table["police_station"] == station)
        & (speed_table["event_cause"] == event_cause)
        & (speed_table["corridor_filled"] == corridor)
    ]
    if len(match):
        return float(match["hist_clearance_min"].iloc[0])
    station_rows = speed_table[speed_table["police_station"] == station]
    if len(station_rows):
        return float(station_rows["hist_clearance_min"].median())
    return fallback_min


def compute_live_loads(
    events_df: pd.DataFrame,
    at_time: datetime | pd.Timestamp,
) -> dict[str, int]:
    ts = pd.Timestamp(at_time)
    if ts.tzinfo is None:
        ts = ts.tz_localize(timezone.utc)
    created = events_df["created_date"]
    closed = events_df["effective_close_datetime"]
    is_open = (created <= ts) & (closed.isna() | (closed > ts))
    open_events = events_df.loc[is_open]
    counts = open_events.groupby("police_station").size()
    return counts.to_dict()


def _normalize(values: list[float], higher_is_better: bool) -> list[float]:
    arr = np.array(values, dtype=float)
    if len(arr) == 0:
        return []
    if arr.max() == arr.min():
        return [1.0] * len(arr)
    scaled = (arr - arr.min()) / (arr.max() - arr.min())
    return (scaled if higher_is_better else 1 - scaled).tolist()


def rank_stations(
    event: dict,
    stats: pd.DataFrame | None = None,
    speed_table: pd.DataFrame | None = None,
    events_df: pd.DataFrame | None = None,
    top_n: int = 5,
) -> list[dict]:
    if stats is None or speed_table is None:
        stats, speed_table = load_station_stats()
    if events_df is None:
        events_df = pd.read_parquet(PREPARED_EVENTS)

    lat = float(event["latitude"])
    lon = float(event["longitude"])
    event_cause = event.get("event_cause", "others")
    corridor = event.get("corridor") or event.get("corridor_filled") or "Non-corridor"

    at_time = event.get("created_date") or event.get("start_datetime")
    if at_time is None:
        live_loads = {}
    else:
        live_loads = compute_live_loads(events_df, pd.Timestamp(at_time))

    global_fallback = float(stats["median_clearance_min"].median(skipna=True))

    distances = []
    loads = []
    clearances = []
    stations = stats["police_station"].tolist()

    for station in stations:
        row = stats.loc[stats["police_station"] == station].iloc[0]
        distances.append(
            float(
                haversine_km(
                    np.array([lat]),
                    np.array([lon]),
                    np.array([row["station_lat"]]),
                    np.array([row["station_lon"]]),
                )[0]
            )
        )
        loads.append(float(live_loads.get(station, 0)))
        clearances.append(
            _lookup_clearance(station, event_cause, corridor, speed_table, global_fallback)
        )

    dist_scores = _normalize(distances, higher_is_better=False)
    load_scores = _normalize(loads, higher_is_better=False)
    speed_scores = _normalize(clearances, higher_is_better=False)

    ranked = []
    for i, station in enumerate(stations):
        breakdown = {
            "distance_km": round(distances[i], 2),
            "live_load": int(loads[i]),
            "station_median_load": int(stats.loc[stats["police_station"] == station, "station_median_load"].iloc[0]),
            "hist_clearance_min": round(clearances[i], 1),
            "distance_score": round(dist_scores[i], 3),
            "load_score": round(load_scores[i], 3),
            "speed_score": round(speed_scores[i], 3),
        }
        total = (
            WEIGHTS["speed"] * speed_scores[i]
            + WEIGHTS["load"] * load_scores[i]
            + WEIGHTS["distance"] * dist_scores[i]
        )
        overloaded = loads[i] > breakdown["station_median_load"]
        ranked.append(
            {
                "police_station": station,
                "total_score": round(total, 3),
                "is_overloaded": overloaded,
                "score_breakdown": breakdown,
            }
        )

    ranked.sort(key=lambda x: x["total_score"], reverse=True)
    return ranked[:top_n]


def recommend_station(
    event: dict,
    stats: pd.DataFrame | None = None,
    speed_table: pd.DataFrame | None = None,
    events_df: pd.DataFrame | None = None,
) -> dict:
    ranked = rank_stations(event, stats, speed_table, events_df, top_n=len(pd.read_csv(STATION_CENTROIDS)))
    recommended = ranked[0]
    rerouted = False
    reroute_reason = None

    for candidate in ranked:
        if not candidate["is_overloaded"]:
            recommended = candidate
            break
    else:
        recommended = ranked[0]

    if ranked[0]["police_station"] != recommended["police_station"]:
        rerouted = True
        reroute_reason = (
            f"{ranked[0]['police_station']} is overloaded "
            f"(load {ranked[0]['score_breakdown']['live_load']} vs median "
            f"{ranked[0]['score_breakdown']['station_median_load']})"
        )

    return {
        "recommended_station": recommended["police_station"],
        "recommended_score": recommended["total_score"],
        "is_overloaded": recommended["is_overloaded"],
        "rerouted_from_overload": rerouted,
        "reroute_reason": reroute_reason,
        "top_candidates": ranked[:5],
        "weights": WEIGHTS,
    }
