"""Heavy-vehicle breakdown risk surface and pre-staging (Modules 6.1 + 6.3)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import (
    BREAKDOWN_SUMMARY,
    CORRIDOR_CENTROIDS,
    PREPARED_EVENTS,
    PRESTAGING_PLAN,
    RISK_SURFACE,
)
from src.spine import haversine_km

REACTIVE_DELAY_MIN = 45.0
PRESTAGE_RADIUS_KM = 8.0
DEFAULT_UNITS = 5


def _breakdown_frame(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["is_breakdown"] == 1].copy()


def build_risk_surface(df: pd.DataFrame) -> pd.DataFrame:
    """Corridor x hour x day risk = frequency x severity."""
    bd = _breakdown_frame(df)
    bd["severity"] = bd["effective_clearance_time_min"].fillna(
        bd["effective_clearance_time_min"].median()
    ) * (1.0 + bd["requires_road_closure"].astype(float) * 0.5)

    surface = (
        bd.groupby(["corridor_filled", "hour_of_day", "day_of_week", "veh_type_filled"], as_index=False)
        .agg(
            event_count=("id", "count"),
            avg_clearance_min=("effective_clearance_time_min", "mean"),
            closure_rate=("requires_road_closure", "mean"),
            avg_severity=("severity", "mean"),
            avg_lat=("latitude", "mean"),
            avg_lon=("longitude", "mean"),
        )
    )
    surface["avg_clearance_min"] = surface["avg_clearance_min"].fillna(
        bd["effective_clearance_time_min"].median()
    )
    surface["avg_severity"] = surface["avg_severity"].fillna(
        surface["avg_clearance_min"] * 1.1
    )
    surface["risk_score"] = surface["event_count"] * surface["avg_severity"]
    surface["risk_rank"] = surface["risk_score"].rank(ascending=False, method="dense")
    return surface.sort_values("risk_score", ascending=False)


def build_corridor_centroids(df: pd.DataFrame) -> pd.DataFrame:
    bd = _breakdown_frame(df)
    bd["severity"] = bd["effective_clearance_time_min"].fillna(
        bd["effective_clearance_time_min"].median()
    ) * (1.0 + bd["requires_road_closure"].astype(float) * 0.5)
    centroids = (
        bd.groupby("corridor_filled", as_index=False)
        .agg(
            corridor_lat=("latitude", "mean"),
            corridor_lon=("longitude", "mean"),
            breakdown_count=("id", "count"),
            corridor_risk=("severity", "sum"),
        )
    )
    return centroids.sort_values("corridor_risk", ascending=False)


def _cell_key(row: pd.Series) -> str:
    return f"{row['corridor_filled']}|{int(row['hour_of_day'])}|{int(row['day_of_week'])}"


def greedy_prestaging(
    surface: pd.DataFrame,
    corridor_centroids: pd.DataFrame,
    n_units: int = DEFAULT_UNITS,
    radius_km: float = PRESTAGE_RADIUS_KM,
) -> tuple[list[dict], dict]:
    """Place units to cover highest remaining corridor-time risk cells."""
    remaining = surface.copy()
    remaining["cell_key"] = remaining.apply(_cell_key, axis=1)
    placements: list[dict] = []
    covered_keys: set[str] = set()

    corridor_lookup = corridor_centroids.set_index("corridor_filled")

    for unit_id in range(1, n_units + 1):
        if remaining.empty:
            break

        best = None
        best_gain = -1.0
        for corridor in remaining["corridor_filled"].unique():
            if corridor not in corridor_lookup.index:
                continue
            centroid = corridor_lookup.loc[corridor]
            clat, clon = centroid["corridor_lat"], centroid["corridor_lon"]
            subset = remaining[remaining["corridor_filled"] == corridor]
            gain = float(subset["risk_score"].sum())
            if gain > best_gain:
                best_gain = gain
                best = {
                    "unit_id": unit_id,
                    "corridor": corridor,
                    "latitude": float(clat),
                    "longitude": float(clon),
                    "covered_risk": gain,
                    "covered_events": int(subset["event_count"].sum()),
                    "peak_hours": sorted(subset["hour_of_day"].unique().tolist()),
                    "peak_days": sorted(subset["day_of_week"].unique().tolist()),
                    "cells_covered": int(len(subset)),
                }

        if best is None:
            break

        placements.append(best)
        corridor_cells = remaining[remaining["corridor_filled"] == best["corridor"]]["cell_key"]
        covered_keys.update(corridor_cells.tolist())

        drop_mask = remaining["cell_key"].isin(covered_keys)
        lat = remaining["avg_lat"].values
        lon = remaining["avg_lon"].values
        for placement in placements:
            dist = haversine_km(
                lat,
                lon,
                np.full(len(remaining), placement["latitude"]),
                np.full(len(remaining), placement["longitude"]),
            )
            drop_mask |= dist <= radius_km
        remaining = remaining.loc[~drop_mask]

    total_events = int(surface["event_count"].sum())
    covered_events = sum(p["covered_events"] for p in placements)
    vehicle_hours_avoided = covered_events * REACTIVE_DELAY_MIN / 60.0

    impact = {
        "reactive_delay_min": REACTIVE_DELAY_MIN,
        "prestage_radius_km": radius_km,
        "units_deployed": len(placements),
        "total_breakdown_events": total_events,
        "covered_breakdown_events": covered_events,
        "coverage_pct": round(100 * covered_events / max(total_events, 1), 1),
        "vehicle_hours_closure_avoided": round(vehicle_hours_avoided, 1),
    }
    return placements, impact


def train(
    df: pd.DataFrame | None = None,
    n_units: int = DEFAULT_UNITS,
) -> dict:
    if df is None:
        df = pd.read_parquet(PREPARED_EVENTS)

    surface = build_risk_surface(df)
    centroids = build_corridor_centroids(df)
    placements, impact = greedy_prestaging(surface, centroids, n_units=n_units)

    RISK_SURFACE.parent.mkdir(parents=True, exist_ok=True)
    surface.to_parquet(RISK_SURFACE, index=False)
    centroids.to_csv(CORRIDOR_CENTROIDS, index=False)
    PRESTAGING_PLAN.write_text(
        json.dumps({"placements": placements, "impact": impact}, indent=2),
        encoding="utf-8",
    )

    summary = {
        "module": "breakdown_risk",
        "risk_cells": int(len(surface)),
        "corridors": int(surface["corridor_filled"].nunique()),
        "top_corridor": surface.iloc[0]["corridor_filled"] if len(surface) else None,
        "impact": impact,
    }
    BREAKDOWN_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def load_risk_surface() -> pd.DataFrame:
    return pd.read_parquet(RISK_SURFACE)


def load_corridor_centroids() -> pd.DataFrame:
    return pd.read_csv(CORRIDOR_CENTROIDS)


def load_prestaging() -> dict:
    return json.loads(PRESTAGING_PLAN.read_text(encoding="utf-8"))


def get_breakdown_risk(
    corridor: str,
    hour: int | None = None,
    day_of_week: int | None = None,
    veh_type: str | None = None,
) -> dict:
    surface = load_risk_surface()
    corridor_key = corridor or "Non-corridor"
    subset = surface[surface["corridor_filled"] == corridor_key]

    if hour is not None:
        subset = subset[subset["hour_of_day"] == int(hour)]
    if day_of_week is not None:
        subset = subset[subset["day_of_week"] == int(day_of_week)]
    if veh_type is not None:
        subset = subset[subset["veh_type_filled"] == veh_type]

    if subset.empty:
        return {
            "corridor": corridor_key,
            "hour": hour,
            "day_of_week": day_of_week,
            "risk_score": 0.0,
            "event_count": 0,
            "risk_level": "low",
            "cells": [],
        }

    total_score = float(subset["risk_score"].sum())
    total_events = int(subset["event_count"].sum())
    max_score = float(surface["risk_score"].max())
    ratio = total_score / max(max_score, 1.0)
    if ratio >= 0.6:
        level = "high"
    elif ratio >= 0.3:
        level = "medium"
    else:
        level = "low"

    top_cells = subset.nlargest(5, "risk_score")
    cells = top_cells[
        [
            "hour_of_day",
            "day_of_week",
            "veh_type_filled",
            "event_count",
            "avg_clearance_min",
            "risk_score",
        ]
    ].to_dict(orient="records")

    return {
        "corridor": corridor_key,
        "hour": hour,
        "day_of_week": day_of_week,
        "risk_score": round(total_score, 1),
        "event_count": total_events,
        "risk_level": level,
        "avg_clearance_min": round(float(subset["avg_clearance_min"].mean()), 1),
        "cells": cells,
    }


def get_corridor_heatmap() -> pd.DataFrame:
    """Aggregate risk by corridor for map choropleth-style display."""
    surface = load_risk_surface()
    return (
        surface.groupby("corridor_filled", as_index=False)
        .agg(
            total_risk=("risk_score", "sum"),
            event_count=("event_count", "sum"),
            avg_clearance_min=("avg_clearance_min", "mean"),
        )
        .sort_values("total_risk", ascending=False)
    )
