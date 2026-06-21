"""Road-closure likelihood model (Spec §5.1 / §7)."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.config import CLOSURE_META, CLOSURE_MODEL, PREPARED_EVENTS

FEATURE_COLS = [
    "event_type",
    "event_cause",
    "priority",
    "zone_filled",
    "junction_filled",
    "corridor_filled",
    "veh_type_filled",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "is_breakdown",
]
CATEGORICAL = [
    "event_type",
    "event_cause",
    "priority",
    "zone_filled",
    "junction_filled",
    "corridor_filled",
    "veh_type_filled",
]
NUMERIC = ["hour_of_day", "day_of_week", "is_weekend", "is_breakdown"]


def _build_pipeline() -> Pipeline:
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL,
            ),
            ("num", "passthrough", NUMERIC),
        ]
    )
    model = HistGradientBoostingClassifier(
        max_depth=6,
        learning_rate=0.1,
        max_iter=150,
        random_state=42,
    )
    return Pipeline([("prep", preprocessor), ("model", model)])


def _prepare_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df[FEATURE_COLS + ["requires_road_closure"]].copy()
    frame["is_breakdown"] = frame["is_breakdown"].astype(int)
    frame["is_weekend"] = frame["is_weekend"].astype(int)
    frame["requires_road_closure"] = frame["requires_road_closure"].astype(int)
    return frame


def train(
    df: pd.DataFrame | None = None,
    model_path: Path = CLOSURE_MODEL,
    meta_path: Path = CLOSURE_META,
) -> tuple[Pipeline, dict]:
    if df is None:
        df = pd.read_parquet(PREPARED_EVENTS)

    frame = _prepare_frame(df)
    x_train, x_test, y_train, y_test = train_test_split(
        frame[FEATURE_COLS],
        frame["requires_road_closure"],
        test_size=0.2,
        random_state=42,
        stratify=frame["requires_road_closure"],
    )

    pipeline = _build_pipeline()
    pipeline.fit(x_train, y_train)
    proba = pipeline.predict_proba(x_test)[:, 1]
    preds = (proba >= 0.5).astype(int)

    meta = {
        "features": FEATURE_COLS,
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "accuracy": float(accuracy_score(y_test, preds)),
        "f1": float(f1_score(y_test, preds, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_test, proba)),
        "baseline_closure_rate": float(frame["requires_road_closure"].mean()),
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return pipeline, meta


def load_model(model_path: Path = CLOSURE_MODEL) -> Pipeline:
    return joblib.load(model_path)


def load_meta(meta_path: Path = CLOSURE_META) -> dict:
    return json.loads(meta_path.read_text(encoding="utf-8"))


def _event_to_frame(event: dict) -> pd.DataFrame:
    row = {
        "event_type": event.get("event_type", "unplanned"),
        "event_cause": event.get("event_cause", "others"),
        "priority": event.get("priority", "High"),
        "zone_filled": event.get("zone") or event.get("zone_filled") or "Unknown",
        "junction_filled": event.get("junction") or event.get("junction_filled") or "Unknown",
        "corridor_filled": event.get("corridor") or event.get("corridor_filled") or "Non-corridor",
        "veh_type_filled": event.get("veh_type") or event.get("veh_type_filled") or "unknown",
        "hour_of_day": int(event.get("hour_of_day", 12)),
        "day_of_week": int(event.get("day_of_week", 0)),
        "is_weekend": int(event.get("is_weekend", 0)),
        "is_breakdown": int(
            event.get("is_breakdown", event.get("event_cause") == "vehicle_breakdown")
        ),
    }
    return pd.DataFrame([row])


def predict_closure(event: dict, pipeline: Pipeline | None = None) -> dict:
    if pipeline is None:
        if not CLOSURE_MODEL.exists():
            return {
                "closure_probability": 0.0,
                "closure_likelihood": "low",
                "model_available": False,
            }
        pipeline = load_model()

    proba = float(pipeline.predict_proba(_event_to_frame(event))[0, 1])
    if proba >= 0.35:
        level = "high"
    elif proba >= 0.12:
        level = "medium"
    else:
        level = "low"

    return {
        "closure_probability": round(proba * 100, 1),
        "closure_likelihood": level,
        "model_available": True,
    }
