"""Unified Smart Dispatch API + retrain loop."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from src.config import (
    BREAKDOWN_SUMMARY,
    CLEARANCE_META,
    CLOSURE_META,
    DISPATCH_SUMMARY,
    PREPARED_EVENTS,
    RETRAIN_HISTORY,
)
from src.models.breakdown_risk import train as train_breakdown
from src.models.clearance_predictor import load_meta as load_clearance_meta
from src.models.clearance_predictor import predict_clearance, train as train_clearance
from src.models.closure_predictor import predict_closure, train as train_closure
from src.models.station_recommender import build_station_stats, recommend_station


def _read_json(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def train_all(df: pd.DataFrame | None = None) -> dict:
    if df is None:
        df = pd.read_parquet(PREPARED_EVENTS)

    _, clearance_meta = train_clearance(df)
    _, closure_meta = train_closure(df)
    build_station_stats(df)

    summary = {
        "module": "smart_dispatch",
        "clearance_model": clearance_meta,
        "closure_model": closure_meta,
        "station_count": int(df["police_station"].nunique()),
    }
    DISPATCH_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    DISPATCH_SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return summary


def retrain_all(df: pd.DataFrame | None = None) -> dict:
    """Closed-loop retrain: capture before/after metrics (Spec §7 / §11)."""
    before = {
        "clearance_mae": _read_json(CLEARANCE_META).get("mae_minutes"),
        "closure_auc": _read_json(CLOSURE_META).get("roc_auc"),
        "breakdown_coverage": _read_json(BREAKDOWN_SUMMARY)
        .get("impact", {})
        .get("coverage_pct"),
    }

    dispatch_summary = train_all(df)
    breakdown_summary = train_breakdown(df)

    after = {
        "clearance_mae": dispatch_summary["clearance_model"]["mae_minutes"],
        "closure_auc": dispatch_summary["closure_model"]["roc_auc"],
        "breakdown_coverage": breakdown_summary["impact"]["coverage_pct"],
    }

    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "before": before,
        "after": after,
        "rows_used": int(len(df) if df is not None else pd.read_parquet(PREPARED_EVENTS)),
    }

    history = _read_json(RETRAIN_HISTORY)
    past = history.get("runs", [])
    past.append(entry)
    RETRAIN_HISTORY.parent.mkdir(parents=True, exist_ok=True)
    RETRAIN_HISTORY.write_text(
        json.dumps({"runs": past[-10:]}, indent=2),
        encoding="utf-8",
    )
    return entry


def load_retrain_history() -> list[dict]:
    return _read_json(RETRAIN_HISTORY).get("runs", [])


def predict_dispatch(event: dict) -> dict:
    """Recommend station, predict clearance + closure likelihood."""
    station = recommend_station(event)
    clearance = predict_clearance(event)
    closure = predict_closure(event)
    return {
        "dispatch": station,
        "clearance_prediction": clearance,
        "closure_prediction": closure,
        "event_summary": {
            "event_cause": event.get("event_cause"),
            "corridor": event.get("corridor") or event.get("corridor_filled"),
            "priority": event.get("priority"),
            "latitude": event.get("latitude"),
            "longitude": event.get("longitude"),
        },
    }


def load_summary(path: Path = DISPATCH_SUMMARY) -> dict:
    return _read_json(path)
