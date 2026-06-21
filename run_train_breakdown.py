"""Train breakdown risk models and pre-staging plan."""

from src.models.breakdown_risk import train


def main() -> None:
    print("EventOps Phase 2B — Breakdown Risk Training")
    print("=" * 44)
    summary = train()
    impact = summary["impact"]
    print(f"  Risk cells:     {summary['risk_cells']}")
    print(f"  Corridors:      {summary['corridors']}")
    print(f"  Top corridor:   {summary['top_corridor']}")
    print(f"  Units deployed: {impact['units_deployed']}")
    print(f"  Coverage:       {impact['coverage_pct']}% of breakdown events")
    print(f"  Vehicle-hours avoided: {impact['vehicle_hours_closure_avoided']}")


if __name__ == "__main__":
    main()
