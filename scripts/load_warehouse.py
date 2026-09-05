"""Load validated landing events into the PulseCommerce warehouse."""

from __future__ import annotations

from pulsecommerce.warehouse.loader import (
    load_events_to_warehouse,
)


def main() -> None:
    """Load landing events and print the quality report."""

    print("PulseCommerce Warehouse Loader")
    print("-" * 50)

    report = load_events_to_warehouse()

    print(f"Total rows: {report.total_rows:,}")
    print(f"Duplicate event IDs: {report.duplicate_event_ids}")
    print(
        "Missing required values: "
        f"{report.missing_required_values}"
    )
    print(
        "Invalid event names: "
        f"{report.invalid_event_names}"
    )
    print(
        "Invalid variants: "
        f"{report.invalid_variants}"
    )
    print(
        "Invalid timestamps: "
        f"{report.invalid_timestamps}"
    )
    print("-" * 50)
    print("Warehouse load completed successfully.")


if __name__ == "__main__":
    main()