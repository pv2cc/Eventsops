"""Build Phase 1 shared data spine."""

from src.config import PREPARED_EVENTS, SPINE_SUMMARY, STATION_CENTROIDS
from src.spine import run


def main() -> None:
    df, centroids, summary = run()
    print("EventOps Phase 1 — Shared Data Spine")
    print("=" * 40)
    for key, value in summary.items():
        print(f"  {key}: {value}")
    print()
    print(f"Prepared events: {PREPARED_EVENTS}")
    print(f"Station centroids: {STATION_CENTROIDS}")
    print(f"Summary: {SPINE_SUMMARY}")
    print()
    print("Sample derived columns:")
    cols = [
        "id",
        "police_station",
        "clearance_time_min",
        "hour_of_day",
        "live_load",
        "distance_to_station_km",
        "is_station_overloaded",
    ]
    print(df[cols].head(5).to_string(index=False))


if __name__ == "__main__":
    main()
