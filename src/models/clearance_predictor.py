"""Clearance-time regression model (Module 5.1)."""

from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from src.config import CLEARANCE_META, CLEARANCE_MODEL, PREPARED_EVENTS

FEATURE_COLS = [
    "event_type",
    "event_cause",
    "priority",
    "zone_filled",
    "junction_filled",
    "corridor_filled",
    "veh_type_filled",
    "requires_road_closure",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "is_breakdown",
]

TARGET_COL = "effective_clearance_time_min"
TRAIN_CAP_MINUTES = 480  # ignore extreme tail during training
CATEGORICAL = [
    "event_type",
    "event_cause",
    "priority",
    "zone_filled",
    "junction_filled",
    "corridor_filled",
    "veh_type_filled",
]
NUMERIC = [
    "requires_road_closure",
    "hour_of_day",
    "day_of_week",
    "is_weekend",
    "is_breakdown",
]


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
    model = HistGradientBoostingRegressor(
        max_depth=8,
        learning_rate=0.08,
        max_iter=200,
        random_state=42,
    )
    return Pipeline([("prep", preprocessor), ("model", model)])


def _prepare_training_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df[FEATURE_COLS + [TARGET_COL]].copy()
    frame["requires_road_closure"] = frame["requires_road_closure"].astype(int)
    frame = frame.dropna(subset=[TARGET_COL])
    return frame[frame[TARGET_COL] <= TRAIN_CAP_MINUTES]


def train(
    df: pd.DataFrame | None = None,
    model_path: Path = CLEARANCE_MODEL,
    meta_path: Path = CLEARANCE_META,
) -> tuple[Pipeline, dict]:
    if df is None:
        df = pd.read_parquet(PREPARED_EVENTS)

    train_df = _prepare_training_frame(df)
    x_train, x_test, y_train, y_test = train_test_split(
        train_df[FEATURE_COLS],
        train_df[TARGET_COL],
        test_size=0.2,
        random_state=42,
    )

    pipeline = _build_pipeline()
    pipeline.fit(x_train, np.log1p(y_train))
    preds = np.expm1(pipeline.predict(x_test))
    residuals = y_test.values - preds
    mae = float(mean_absolute_error(y_test, preds))
    rmse = float(np.sqrt(mean_squared_error(y_test, preds)))

    meta = {
        "target": TARGET_COL,
        "features": FEATURE_COLS,
        "train_rows": int(len(x_train)),
        "test_rows": int(len(x_test)),
        "mae_minutes": mae,
        "rmse_minutes": rmse,
        "residual_p10": float(np.percentile(residuals, 10)),
        "residual_p90": float(np.percentile(residuals, 90)),
        "median_predicted_min": float(np.median(np.expm1(pipeline.predict(x_train)))),
        "train_cap_minutes": TRAIN_CAP_MINUTES,
        "target_transform": "log1p",
    }

    model_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_path)
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")
    return pipeline, meta


def load_model(model_path: Path = CLEARANCE_MODEL) -> Pipeline:
    return joblib.load(model_path)


def load_meta(meta_path: Path = CLEARANCE_META) -> dict:
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
        "requires_road_closure": int(bool(event.get("requires_road_closure", False))),
        "hour_of_day": int(event.get("hour_of_day", 12)),
        "day_of_week": int(event.get("day_of_week", 0)),
        "is_weekend": int(event.get("is_weekend", 0)),
        "is_breakdown": int(
            event.get("is_breakdown", event.get("event_cause") == "vehicle_breakdown")
        ),
    }
    return pd.DataFrame([row])


def predict_clearance(
    event: dict,
    pipeline: Pipeline | None = None,
    meta: dict | None = None,
) -> dict:
    if pipeline is None:
        pipeline = load_model()
    if meta is None:
        meta = load_meta()

    point = float(np.expm1(pipeline.predict(_event_to_frame(event)))[0])
    low = max(0.0, point + meta["residual_p10"])
    high = max(low, point + meta["residual_p90"])
    return {
        "predicted_clearance_min": round(point, 1),
        "confidence_low_min": round(low, 1),
        "confidence_high_min": round(high, 1),
    }
