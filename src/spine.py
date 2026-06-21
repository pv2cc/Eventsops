"""Shared data spine: durations, station centroids, live load, time features."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import PREPARED_EVENTS, RAW_CSV, SPINE_SUMMARY, STATION_CENTROIDS

DATETIME_COLS = [
    "start_datetime",
    "end_datetime",
    "created_date",
    "modified_datetime",
    "closed_datetime",
    "resolved_datetime",
]

MAX_CLEARANCE_MINUTES = 7 * 24 * 60  # cap at one week


def haversine_km(
    lat1: pd.Series | np.ndarray,
    lon1: pd.Series | np.ndarray,
    lat2: pd.Series | np.ndarray,
    lon2: pd.Series | np.ndarray,
) -> np.ndarray:
    """Great-circle distance in kilometres."""
    lat1_rad = np.radians(lat1)
    lon1_rad = np.radians(lon1)
    lat2_rad = np.radians(lat2)
    lon2_rad = np.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def load_raw(csv_path: Path = RAW_CSV) -> pd.DataFrame:
    df = pd.read_csv(csv_path, low_memory=False)
    for col in DATETIME_COLS:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], utc=True, errors="coerce")
    return df


def add_effective_close(df: pd.DataFrame) -> pd.DataFrame:
    """Impute end time when closed_datetime is missing but the event is finished."""
    out = df.copy()
    closed_like = out["status"].isin(["closed", "resolved"])
    out["effective_close_datetime"] = out["closed_datetime"]
    missing_close = closed_like & out["effective_close_datetime"].isna()
    out.loc[missing_close, "effective_close_datetime"] = out.loc[
        missing_close, "modified_datetime"
    ]
    return out


def add_duration_labels(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["resolution_time_min"] = (
        (out["resolved_datetime"] - out["start_datetime"]).dt.total_seconds() / 60
    )
    out["clearance_time_min"] = (
        (out["closed_datetime"] - out["created_date"]).dt.total_seconds() / 60
    )
    out["effective_clearance_time_min"] = (
        (out["effective_close_datetime"] - out["created_date"]).dt.total_seconds() / 60
    )

    valid_resolution = out["resolution_time_min"].between(0, MAX_CLEARANCE_MINUTES)
    valid_clearance = out["clearance_time_min"].between(0, MAX_CLEARANCE_MINUTES)
    valid_effective = out["effective_clearance_time_min"].between(0, MAX_CLEARANCE_MINUTES)
    out.loc[~valid_resolution, "resolution_time_min"] = np.nan
    out.loc[~valid_clearance, "clearance_time_min"] = np.nan
    out.loc[~valid_effective, "effective_clearance_time_min"] = np.nan
    return out


def add_time_features(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    ref = out["start_datetime"].fillna(out["created_date"])
    out["hour_of_day"] = ref.dt.hour
    out["day_of_week"] = ref.dt.dayofweek
    out["is_weekend"] = out["day_of_week"].isin([5, 6]).astype(int)
    out["month"] = ref.dt.month
    return out


def add_geo_buckets(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["zone_filled"] = out["zone"].fillna("Unknown").astype(str)
    out["junction_filled"] = out["junction"].fillna("Unknown").astype(str)
    out["corridor_filled"] = out["corridor"].fillna("Non-corridor").astype(str)
    return out


def build_station_centroids(df: pd.DataFrame) -> pd.DataFrame:
    centroids = (
        df.groupby("police_station", as_index=False)
        .agg(
            station_lat=("latitude", "mean"),
            station_lon=("longitude", "mean"),
            station_event_count=("id", "count"),
            median_clearance_min=("effective_clearance_time_min", "median"),
        )
        .sort_values("station_event_count", ascending=False)
    )
    return centroids


def attach_station_geo(df: pd.DataFrame, centroids: pd.DataFrame) -> pd.DataFrame:
    out = df.merge(centroids, on="police_station", how="left")
    out["distance_to_station_km"] = haversine_km(
        out["latitude"].values,
        out["longitude"].values,
        out["station_lat"].values,
        out["station_lon"].values,
    )
    return out


def _live_load_for_station(group: pd.DataFrame) -> pd.DataFrame:
    group = group.sort_values("created_date").copy()
    created = group["created_date"].values
    closed = group["effective_close_datetime"].values
    loads = np.zeros(len(group), dtype=int)

    for i, t in enumerate(created):
        is_open = (created <= t) & ((pd.isna(closed)) | (closed > t))
        loads[i] = int(is_open.sum())

    group["live_load"] = loads
    return group


def add_live_load(df: pd.DataFrame) -> pd.DataFrame:
    parts = [
        _live_load_for_station(group)
        for _, group in df.groupby("police_station", sort=False)
    ]
    out = pd.concat(parts).sort_index()
    return out


def add_station_load_baselines(df: pd.DataFrame) -> pd.DataFrame:
    station_stats = (
        df.groupby("police_station")["live_load"]
        .agg(station_median_load="median", station_max_load="max")
        .reset_index()
    )
    out = df.merge(station_stats, on="police_station", how="left")
    out["is_station_overloaded"] = (
        out["live_load"] > out["station_median_load"]
    ).astype(int)
    return out


def add_breakdown_flags(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["is_breakdown"] = (out["event_cause"] == "vehicle_breakdown").astype(int)
    out["veh_type_filled"] = out["veh_type"].fillna("unknown").astype(str)
    return out


def build_spine(csv_path: Path = RAW_CSV) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    raw = load_raw(csv_path)
    df = (
        raw.pipe(add_effective_close)
        .pipe(add_duration_labels)
        .pipe(add_time_features)
        .pipe(add_geo_buckets)
    )
    centroids = build_station_centroids(df)
    df = (
        df.pipe(attach_station_geo, centroids)
        .pipe(add_live_load)
        .pipe(add_station_load_baselines)
        .pipe(add_breakdown_flags)
    )

    summary = {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "unique_stations": int(df["police_station"].nunique()),
        "clearance_time_available": int(df["clearance_time_min"].notna().sum()),
        "effective_clearance_available": int(df["effective_clearance_time_min"].notna().sum()),
        "resolution_time_available": int(df["resolution_time_min"].notna().sum()),
        "median_clearance_min": float(df["clearance_time_min"].median(skipna=True))
        if df["clearance_time_min"].notna().any()
        else None,
        "median_effective_clearance_min": float(
            df["effective_clearance_time_min"].median(skipna=True)
        )
        if df["effective_clearance_time_min"].notna().any()
        else None,
        "median_live_load": float(df["live_load"].median()),
        "overloaded_event_pct": float(df["is_station_overloaded"].mean() * 100),
        "breakdown_events": int(df["is_breakdown"].sum()),
    }
    return df, centroids, summary


def save_spine(
    df: pd.DataFrame,
    centroids: pd.DataFrame,
    summary: dict,
    events_path: Path = PREPARED_EVENTS,
    centroids_path: Path = STATION_CENTROIDS,
    summary_path: Path = SPINE_SUMMARY,
) -> None:
    events_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(events_path, index=False)
    centroids.to_csv(centroids_path, index=False)
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def run(csv_path: Path = RAW_CSV) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    df, centroids, summary = build_spine(csv_path)
    save_spine(df, centroids, summary)
    return df, centroids, summary
