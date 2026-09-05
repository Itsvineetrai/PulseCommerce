"""Run PulseCommerce behavioral analytics models."""

from __future__ import annotations

from pulsecommerce.analytics.runner import run_analytics_models


def main() -> None:
    """Execute all behavioral analytics models."""

    print("PulseCommerce Behavioral Analytics")
    print("-" * 50)

    run_analytics_models()

    print("Analytics models completed successfully.")
    print("Created warehouse tables:")
    print("  - analytics_session_funnel")
    print("  - analytics_funnel_metrics")
    print("  - analytics_velocity_metrics")


if __name__ == "__main__":
    main()