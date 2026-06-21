"""Train all EventOps models (dispatch + closure + breakdown)."""

from src.models.breakdown_risk import train as train_breakdown
from src.models.dispatch_service import train_all as train_dispatch


def main() -> None:
    print("Training Smart Dispatch + Closure...")
    train_dispatch()
    print("Training Breakdown Risk...")
    train_breakdown()
    print("Done. Launch dashboard: python -m streamlit run app.py")


if __name__ == "__main__":
    main()
