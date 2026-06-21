"""Recurring incident patterns for the learning-loop narrative."""

from __future__ import annotations

import pandas as pd

from src.config import PREPARED_EVENTS

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def recurring_patterns(df: pd.DataFrame | None = None, top_n: int = 10) -> pd.DataFrame:
    if df is None:
        df = pd.read_parquet(PREPARED_EVENTS)

    patterns = (
        df.groupby(["corridor_filled", "event_cause", "hour_of_day"], as_index=False)
        .agg(
            event_count=("id", "count"),
            avg_clearance_min=("effective_clearance_time_min", "mean"),
            closure_rate=("requires_road_closure", "mean"),
            avg_live_load=("live_load", "mean"),
        )
        .sort_values("event_count", ascending=False)
        .head(top_n)
    )
    patterns["avg_clearance_min"] = patterns["avg_clearance_min"].round(1)
    patterns["closure_rate"] = (patterns["closure_rate"] * 100).round(1)
    patterns["avg_live_load"] = patterns["avg_live_load"].round(1)
    patterns["peak_window"] = patterns["hour_of_day"].apply(
        lambda h: f"{int(h):02d}:00"
    )
    return patterns[
        [
            "corridor_filled",
            "event_cause",
            "peak_window",
            "event_count",
            "avg_clearance_min",
            "closure_rate",
            "avg_live_load",
        ]
    ]


def peak_windows_for_corridor(corridor: str, df: pd.DataFrame | None = None, top_n: int = 3) -> list[dict]:
    if df is None:
        df = pd.read_parquet(PREPARED_EVENTS)

    bd = df[(df["corridor_filled"] == corridor) & (df["is_breakdown"] == 1)]
    if bd.empty:
        return []

    windows = (
        bd.groupby(["hour_of_day", "day_of_week"], as_index=False)
        .agg(events=("id", "count"), avg_clearance=("effective_clearance_time_min", "mean"))
        .sort_values("events", ascending=False)
        .head(top_n)
    )
    return [
        {
            "hour": int(row["hour_of_day"]),
            "day": DAY_NAMES[int(row["day_of_week"])],
            "events": int(row["events"]),
            "avg_clearance_min": round(float(row["avg_clearance"]), 1),
        }
        for _, row in windows.iterrows()
    ]
