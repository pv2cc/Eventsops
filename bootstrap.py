"""Ensure data spine and trained models exist (first run / cloud deploy)."""

from __future__ import annotations

from src.config import (
    BREAKDOWN_SUMMARY,
    CLEARANCE_MODEL,
    DISPATCH_SUMMARY,
    PREPARED_EVENTS,
    PRESTAGING_PLAN,
    RISK_SURFACE,
)


def artifacts_ready() -> bool:
    return all(
        p.exists()
        for p in (
            PREPARED_EVENTS,
            CLEARANCE_MODEL,
            DISPATCH_SUMMARY,
            RISK_SURFACE,
            PRESTAGING_PLAN,
            BREAKDOWN_SUMMARY,
        )
    )


def ensure_artifacts(force: bool = False) -> None:
    if not force and artifacts_ready():
        return

    from run_spine import main as run_spine_main
    from run_train_all import main as run_train_main

    if force or not PREPARED_EVENTS.exists():
        run_spine_main()
    if force or not CLEARANCE_MODEL.exists():
        run_train_main()
