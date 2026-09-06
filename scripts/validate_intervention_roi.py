"""Validate intervention ROI output for PulseCommerce."""

from __future__ import annotations

from pathlib import Path

import duckdb


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)

FLOAT_TOLERANCE = 1e-6


def load_validation_datasets():
    """Load portfolio and ROI datasets from the warehouse."""

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        portfolio = connection.execute(
            """
            SELECT *
            FROM analytics_intervention_portfolio
            """
        ).fetchdf()

        roi_dataset = connection.execute(
            """
            SELECT *
            FROM analytics_intervention_roi
            """
        ).fetchdf()

        return portfolio, roi_dataset

    finally:
        connection.close()


def main() -> None:
    """Run intervention ROI validation checks."""

    print("PulseCommerce Intervention ROI Validation")
    print("-" * 60)

    portfolio, roi_dataset = load_validation_datasets()

    print()
    print("1. ROW AND PORTFOLIO RECONCILIATION")

    portfolio_rows = len(portfolio)
    roi_rows = len(roi_dataset)

    row_difference = roi_rows - portfolio_rows

    print(f"Portfolio rows: {portfolio_rows:,}")
    print(f"ROI rows:       {roi_rows:,}")
    print(f"Row difference: {row_difference:,}")

    if row_difference != 0:
        raise ValueError(
            "Portfolio and ROI row counts do not match."
        )

    print()
    print("2. DUPLICATE SESSION CHECK")

    duplicate_sessions = (
        roi_dataset["session_id"]
        .duplicated()
        .sum()
    )

    print(
        f"Duplicate sessions: "
        f"{duplicate_sessions:,}"
    )

    if duplicate_sessions != 0:
        raise ValueError(
            "Duplicate sessions found in ROI dataset."
        )

    print()
    print("3. SESSION RECONCILIATION")

    portfolio_sessions = set(
        portfolio["session_id"]
    )

    roi_sessions = set(
        roi_dataset["session_id"]
    )

    missing_from_roi = (
        portfolio_sessions - roi_sessions
    )

    unexpected_roi_sessions = (
        roi_sessions - portfolio_sessions
    )

    print(
        f"Portfolio sessions missing ROI: "
        f"{len(missing_from_roi):,}"
    )

    print(
        f"Unexpected ROI sessions: "
        f"{len(unexpected_roi_sessions):,}"
    )

    if missing_from_roi:
        raise ValueError(
            "Portfolio sessions are missing from ROI dataset."
        )

    if unexpected_roi_sessions:
        raise ValueError(
            "Unexpected sessions found in ROI dataset."
        )

    print()
    print("4. REQUIRED VALUE CHECK")

    required_columns = [
        "expected_recovery_value",
        "intervention_cost",
        "expected_net_value",
        "roi_pct",
    ]

    missing_values = (
        roi_dataset[required_columns]
        .isna()
        .sum()
        .sum()
    )

    print(
        f"Missing required values: "
        f"{missing_values:,}"
    )

    if missing_values != 0:
        raise ValueError(
            "Missing values found in ROI dataset."
        )

    print()
    print("5. VALUE RANGE CHECK")

    negative_recovery_values = (
        roi_dataset["expected_recovery_value"] < 0
    ).sum()

    negative_costs = (
        roi_dataset["intervention_cost"] < 0
    ).sum()

    print(
        f"Negative recovery values: "
        f"{negative_recovery_values:,}"
    )

    print(
        f"Negative intervention costs: "
        f"{negative_costs:,}"
    )

    if negative_recovery_values != 0:
        raise ValueError(
            "Negative expected recovery values found."
        )

    if negative_costs != 0:
        raise ValueError(
            "Negative intervention costs found."
        )

    print()
    print("6. NET VALUE FORMULA RECONCILIATION")

    calculated_net_value = (
        roi_dataset["expected_recovery_value"]
        - roi_dataset["intervention_cost"]
    )

    net_value_difference = (
        calculated_net_value
        - roi_dataset["expected_net_value"]
    ).abs()

    invalid_net_value_rows = (
        net_value_difference > FLOAT_TOLERANCE
    ).sum()

    print(
        f"Invalid net value rows: "
        f"{invalid_net_value_rows:,}"
    )

    if invalid_net_value_rows != 0:
        raise ValueError(
            "Expected net value formula reconciliation failed."
        )

    print()
    print("7. ROI ZERO-COST CONTRACT")

    zero_cost_rows = (
        roi_dataset["intervention_cost"] == 0
    )

    invalid_zero_cost_roi_rows = (
        roi_dataset.loc[
            zero_cost_rows,
            "roi_pct",
        ].abs()
        > FLOAT_TOLERANCE
    ).sum()

    print(
        f"Invalid zero-cost ROI rows: "
        f"{invalid_zero_cost_roi_rows:,}"
    )

    if invalid_zero_cost_roi_rows != 0:
        raise ValueError(
            "ROI must be zero when intervention cost is zero."
        )

    print()
    print("8. ROI FORMULA RECONCILIATION")

    positive_cost_rows = (
        roi_dataset["intervention_cost"] > 0
    )

    calculated_roi = (
        roi_dataset.loc[
            positive_cost_rows,
            "expected_net_value",
        ]
        / roi_dataset.loc[
            positive_cost_rows,
            "intervention_cost",
        ]
        * 100
    )

    roi_difference = (
        calculated_roi
        - roi_dataset.loc[
            positive_cost_rows,
            "roi_pct",
        ]
    ).abs()

    invalid_roi_rows = (
        roi_difference > FLOAT_TOLERANCE
    ).sum()

    print(
        f"Invalid ROI formula rows: "
        f"{invalid_roi_rows:,}"
    )

    if invalid_roi_rows != 0:
        raise ValueError(
            "ROI formula reconciliation failed."
        )

    print()
    print("9. TOTAL PORTFOLIO RECONCILIATION")

    total_recovery_value = (
        roi_dataset[
            "expected_recovery_value"
        ].sum()
    )

    total_intervention_cost = (
        roi_dataset[
            "intervention_cost"
        ].sum()
    )

    total_expected_net_value = (
        roi_dataset[
            "expected_net_value"
        ].sum()
    )

    total_difference = abs(
        (
            total_recovery_value
            - total_intervention_cost
        )
        - total_expected_net_value
    )

    print(
        f"Total expected recovery value: "
        f"{total_recovery_value:.2f}"
    )

    print(
        f"Total intervention cost: "
        f"{total_intervention_cost:.2f}"
    )

    print(
        f"Total expected net value: "
        f"{total_expected_net_value:.2f}"
    )

    print(
        f"Portfolio reconciliation difference: "
        f"{total_difference:.10f}"
    )

    if total_difference > FLOAT_TOLERANCE:
        raise ValueError(
            "Portfolio total reconciliation failed."
        )

    print()
    print("10. FINAL VALIDATION")

    print()
    print("PHASE 6 ROI VALIDATION PASSED")


if __name__ == "__main__":
    main()