"""Train Phase 2 Smart Dispatch models."""

from src.models.dispatch_service import predict_dispatch, train_all


def main() -> None:
    print("EventOps Phase 2 — Smart Dispatch Training")
    print("=" * 44)
    summary = train_all()
    print(f"  MAE (min):  {summary['clearance_model']['mae_minutes']:.1f}")
    print(f"  RMSE (min): {summary['clearance_model']['rmse_minutes']:.1f}")
    print(f"  Train rows: {summary['clearance_model']['train_rows']}")
    print(f"  Stations:   {summary['station_count']}")
    print()

    sample_event = {
        "latitude": 13.0400041,
        "longitude": 77.5180991,
        "event_type": "unplanned",
        "event_cause": "vehicle_breakdown",
        "priority": "High",
        "corridor": "Tumkur Road",
        "veh_type": "lcv",
        "requires_road_closure": False,
        "hour_of_day": 17,
        "day_of_week": 3,
        "is_weekend": 0,
        "created_date": "2024-03-07T17:03:51Z",
    }
    result = predict_dispatch(sample_event)
    print("Sample dispatch JSON:")
    import json

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
