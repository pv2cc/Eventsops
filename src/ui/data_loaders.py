"""Cached data loaders for Streamlit UI."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from src.config import BREAKDOWN_SUMMARY, DISPATCH_SUMMARY, PREPARED_EVENTS


@st.cache_data
def load_events() -> pd.DataFrame:
    return pd.read_parquet(PREPARED_EVENTS)


@st.cache_data
def load_summaries() -> tuple[dict, dict]:
    dispatch: dict = {}
    breakdown: dict = {"impact": {}}
    if DISPATCH_SUMMARY.exists():
        dispatch = json.loads(DISPATCH_SUMMARY.read_text(encoding="utf-8"))
    if BREAKDOWN_SUMMARY.exists():
        breakdown = json.loads(BREAKDOWN_SUMMARY.read_text(encoding="utf-8"))
    return dispatch, breakdown
