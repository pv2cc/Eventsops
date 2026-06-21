"""Before/after impact and manpower estimates for judge-facing metrics."""

from __future__ import annotations

REACTIVE_DELAY_MIN = 45.0
PREVENTIVE_DELAY_MIN = 5.0
OFFICER_HOURS_PER_VEH_HR = 0.35
DATASET_WEEKS = 21.4  # ASTraM record spans ~150 days


def corridor_in_prestage_plan(corridor: str, prestaging: dict) -> bool:
    corridors = {p["corridor"] for p in prestaging.get("placements", [])}
    return corridor in corridors


def compute_before_after(
    predicted_clearance_min: float,
    prestaging_impact: dict,
    corridor: str,
    prestaging: dict | None = None,
) -> dict:
    """Compare reactive vs preventive response for a single incident."""
    in_zone = corridor_in_prestage_plan(corridor, prestaging or {"placements": []})

    reactive_total = REACTIVE_DELAY_MIN + predicted_clearance_min
    preventive_delay = PREVENTIVE_DELAY_MIN if in_zone else REACTIVE_DELAY_MIN * 0.5
    preventive_clearance = predicted_clearance_min * (0.88 if in_zone else 0.95)
    preventive_total = preventive_delay + preventive_clearance

    minutes_saved = max(0.0, reactive_total - preventive_total)
    total_veh_hrs = float(prestaging_impact.get("vehicle_hours_closure_avoided", 0))
    weeks = float(prestaging_impact.get("dataset_weeks", DATASET_WEEKS)) or DATASET_WEEKS
    weekly_veh_hrs = round(total_veh_hrs / weeks, 1)
    total_officer_hrs = round(total_veh_hrs * OFFICER_HOURS_PER_VEH_HR, 1)
    weekly_officer_hrs = round(weekly_veh_hrs * OFFICER_HOURS_PER_VEH_HR, 1)

    return {
        "reactive": {
            "response_delay_min": REACTIVE_DELAY_MIN,
            "clearance_min": round(predicted_clearance_min, 1),
            "total_min": round(reactive_total, 1),
        },
        "preventive": {
            "response_delay_min": round(preventive_delay, 1),
            "clearance_min": round(preventive_clearance, 1),
            "total_min": round(preventive_total, 1),
            "pre_staged_corridor": in_zone,
        },
        "minutes_saved_per_incident": round(minutes_saved, 1),
        "vehicle_hours_avoided_total": round(total_veh_hrs, 1),
        "vehicle_hours_avoided_per_week": weekly_veh_hrs,
        "officer_hours_saved_total": total_officer_hrs,
        "officer_hours_saved_per_week": weekly_officer_hrs,
        "dataset_weeks": weeks,
        "coverage_pct": prestaging_impact.get("coverage_pct", 0),
    }


def overload_manpower_note(rerouted: bool) -> str:
    if rerouted:
        return "Overload reroute avoids stacking officers at a saturated station."
    return "Selected station is within normal load — no reroute needed."
