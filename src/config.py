from pathlib import Path
import os

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

DATA_DIR = ROOT / "data"
MODELS_DIR = DATA_DIR / "models"
RAW_CSV = ROOT / "Astram event data_anonymized - Astram event data_anonymizedb40ac87.csv"
PREPARED_EVENTS = DATA_DIR / "prepared_events.parquet"
STATION_CENTROIDS = DATA_DIR / "station_centroids.csv"
SPINE_SUMMARY = DATA_DIR / "spine_summary.json"
CLEARANCE_MODEL = MODELS_DIR / "clearance_model.joblib"
CLEARANCE_META = MODELS_DIR / "clearance_meta.json"
STATION_STATS = MODELS_DIR / "station_stats.parquet"
DISPATCH_SUMMARY = MODELS_DIR / "dispatch_summary.json"
RISK_SURFACE = MODELS_DIR / "risk_surface.parquet"
CORRIDOR_CENTROIDS = DATA_DIR / "corridor_centroids.csv"
PRESTAGING_PLAN = MODELS_DIR / "prestaging_plan.json"
BREAKDOWN_SUMMARY = MODELS_DIR / "breakdown_summary.json"
CLOSURE_MODEL = MODELS_DIR / "closure_model.joblib"
CLOSURE_META = MODELS_DIR / "closure_meta.json"
RETRAIN_HISTORY = MODELS_DIR / "retrain_history.json"
def _secret(name: str) -> str:
    try:
        import streamlit as st

        if name in st.secrets:
            return str(st.secrets[name]).strip()
    except Exception:
        pass
    return ""


MAPMYINDIA_API_KEY = os.getenv("MAPMYINDIA_API_KEY", "").strip() or _secret("MAPMYINDIA_API_KEY")
MAPPLS_CLIENT_ID = os.getenv("MAPPLS_CLIENT_ID", "").strip() or _secret("MAPPLS_CLIENT_ID")
MAPPLS_CLIENT_SECRET = os.getenv("MAPPLS_CLIENT_SECRET", "").strip() or _secret("MAPPLS_CLIENT_SECRET")
MAPPLS_MAP_HTML = DATA_DIR / "mappls_dashboard.html"
