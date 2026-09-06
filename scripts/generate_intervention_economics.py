"""Generate PulseCommerce intervention economics."""

from __future__ import annotations

from pathlib import Path

import duckdb

from pulsecommerce.intervention.economics_service import (
    calculate_intervention_economics,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


def load_intervention_dataset():
    """Load intervention candidates with cart value."""

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        return connection.execute(
            """
            WITH session_cart_value AS (
                SELECT
                    session_id,
                    MAX(
                        COALESCE(
                            cart_value,
                            0
                        )
                    ) AS cart_value
                FROM events
                GROUP BY session_id
            )

            SELECT
                candidates.user_id,
                candidates.session_id,
                candidates.observation_timestamp,
                candidates.recommended_action,
                candidates.intervention_priority,
                candidates.risk_band,
                candidates.churn_probability,
                candidates.churn_risk_score,
                COALESCE(
                    cart_values.cart_value,
                    0
                ) AS cart_value
            FROM analytics_intervention_candidates
                AS candidates
            LEFT JOIN session_cart_value
                AS cart_values
                ON candidates.session_id
                = cart_values.session_id
            """
        ).fetchdf()

    finally:
        connection.close()


def save_intervention_economics(
    economics,
) -> None:
    """Persist intervention economics."""

    connection = duckdb.connect(
        str(DATABASE_PATH)
    )

    try:
        connection.register(
            "intervention_economics_df",
            economics,
        )

        connection.execute(
            """
            CREATE OR REPLACE TABLE
            analytics_intervention_economics AS
            SELECT *
            FROM intervention_economics_df
            """
        )

        connection.unregister(
            "intervention_economics_df"
        )

    finally:
        connection.close()


def main() -> None:
    """Generate intervention economics."""

    print(
        "PulseCommerce Intervention Economics"
    )

    print("-" * 60)

    dataset = load_intervention_dataset()

    print()
    print(
        "1. LOADED INTERVENTION SESSIONS"
    )

    print(
        f"Sessions: {len(dataset):,}"
    )

    economics = (
        calculate_intervention_economics(
            dataset
        )
    )

    save_intervention_economics(
        economics
    )

    print()
    print(
        "2. ECONOMIC VALUE BY ACTION"
    )

    summary = economics.groupby(
        "recommended_action",
        as_index=False,
    ).agg(
        sessions=(
            "session_id",
            "count",
        ),
        avg_cart_value=(
            "cart_value",
            "mean",
        ),
        total_expected_recovery_value=(
            "expected_recovery_value",
            "sum",
        ),
        total_intervention_cost=(
            "intervention_cost",
            "sum",
        ),
        total_expected_net_value=(
            "expected_net_value",
            "sum",
        ),
    )

    print(
        summary.round(
            2
        ).to_string(
            index=False
        )
    )

    print()
    print(
        "3. TOP 10 INTERVENTION OPPORTUNITIES"
    )

    top_opportunities = economics.sort_values(
        "business_priority_score",
        ascending=False,
    ).head(10)

    print(
        top_opportunities[
            [
                "session_id",
                "recommended_action",
                "churn_risk_score",
                "cart_value",
                "expected_net_value",
                "business_priority_score",
            ]
        ]
        .round(2)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "INTERVENTION ECONOMICS GENERATION COMPLETE"
    )


if __name__ == "__main__":
    main()