"""Generate intervention ROI analysis for PulseCommerce."""

from __future__ import annotations

from pathlib import Path

import duckdb

from pulsecommerce.intervention.roi_service import (
    calculate_intervention_roi,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


def load_intervention_portfolio():
    """Load optimized intervention portfolio."""

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        return connection.execute(
            """
            SELECT *
            FROM analytics_intervention_portfolio
            """
        ).fetchdf()

    finally:
        connection.close()


def save_intervention_roi(
    roi_dataset,
) -> None:
    """Save intervention ROI analysis."""

    connection = duckdb.connect(
        str(DATABASE_PATH)
    )

    try:
        connection.register(
            "intervention_roi_df",
            roi_dataset,
        )

        connection.execute(
            """
            CREATE OR REPLACE TABLE
            analytics_intervention_roi AS
            SELECT *
            FROM intervention_roi_df
            """
        )

        connection.unregister(
            "intervention_roi_df"
        )

    finally:
        connection.close()


def main() -> None:
    """Generate intervention ROI analysis."""

    print(
        "PulseCommerce Intervention ROI Analysis"
    )

    print("-" * 60)

    portfolio = (
        load_intervention_portfolio()
    )

    print()
    print(
        "1. LOADED OPTIMIZED PORTFOLIO"
    )

    print(
        f"Selected sessions: {len(portfolio):,}"
    )

    roi_dataset = (
        calculate_intervention_roi(
            portfolio
        )
    )

    save_intervention_roi(
        roi_dataset
    )

    print()
    print(
        "2. PORTFOLIO INVESTMENT SUMMARY"
    )

    total_expected_recovery = (
        roi_dataset[
            "expected_recovery_value"
        ].sum()
    )

    total_cost = (
        roi_dataset[
            "intervention_cost"
        ].sum()
    )

    total_net_value = (
        roi_dataset[
            "expected_net_value"
        ].sum()
    )

    overall_roi_pct = 0.0

    if total_cost > 0:
        overall_roi_pct = (
            total_net_value
            / total_cost
            * 100
        )

    print(
        f"Expected recovered value: "
        f"{total_expected_recovery:.2f}"
    )

    print(
        f"Total intervention cost: "
        f"{total_cost:.2f}"
    )

    print(
        f"Expected net value: "
        f"{total_net_value:.2f}"
    )

    print(
        f"Expected ROI: "
        f"{overall_roi_pct:.2f}%"
    )

    print()
    print(
        "3. ROI BY INTERVENTION ACTION"
    )

    action_summary = (
        roi_dataset.groupby(
            "recommended_action",
            as_index=False,
        )
        .agg(
            sessions=(
                "session_id",
                "count",
            ),
            expected_recovery_value=(
                "expected_recovery_value",
                "sum",
            ),
            intervention_cost=(
                "intervention_cost",
                "sum",
            ),
            expected_net_value=(
                "expected_net_value",
                "sum",
            ),
        )
    )

    action_summary[
        "roi_pct"
    ] = 0.0

    action_cost_mask = (
        action_summary[
            "intervention_cost"
        ] > 0
    )

    action_summary.loc[
        action_cost_mask,
        "roi_pct",
    ] = (
        action_summary.loc[
            action_cost_mask,
            "expected_net_value",
        ]
        / action_summary.loc[
            action_cost_mask,
            "intervention_cost",
        ]
        * 100
    )

    print(
        action_summary
        .round(2)
        .sort_values(
            "expected_net_value",
            ascending=False,
        )
        .to_string(
            index=False
        )
    )

    print()
    print(
        "4. TOP 10 ROI OPPORTUNITIES"
    )

    top_roi = roi_dataset.sort_values(
        "roi_pct",
        ascending=False,
    ).head(10)

    print(
        top_roi[
            [
                "portfolio_rank",
                "session_id",
                "recommended_action",
                "cart_value",
                "expected_recovery_value",
                "intervention_cost",
                "expected_net_value",
                "roi_pct",
            ]
        ]
        .round(2)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "INTERVENTION ROI ANALYSIS COMPLETE"
    )


if __name__ == "__main__":
    main()