"""Generate optimized intervention portfolio for PulseCommerce."""

from __future__ import annotations

from pathlib import Path

import duckdb

from pulsecommerce.intervention.optimization_service import (
    DEFAULT_INTERVENTION_CAPACITY,
    optimize_intervention_portfolio,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


def load_intervention_economics():
    """Load intervention economics from the warehouse."""

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        return connection.execute(
            """
            SELECT *
            FROM analytics_intervention_economics
            """
        ).fetchdf()

    finally:
        connection.close()


def save_intervention_portfolio(
    portfolio,
) -> None:
    """Save optimized portfolio to DuckDB."""

    connection = duckdb.connect(
        str(DATABASE_PATH)
    )

    try:
        connection.register(
            "portfolio_df",
            portfolio,
        )

        connection.execute(
            """
            CREATE OR REPLACE TABLE
            analytics_intervention_portfolio AS
            SELECT *
            FROM portfolio_df
            """
        )

        connection.unregister(
            "portfolio_df"
        )

    finally:
        connection.close()


def main() -> None:
    """Generate intervention portfolio."""

    print(
        "PulseCommerce Intervention Portfolio"
    )

    print("-" * 60)

    economics = (
        load_intervention_economics()
    )

    print()
    print(
        "1. LOADED INTERVENTION ECONOMICS"
    )

    print(
        f"Total sessions: {len(economics):,}"
    )

    eligible = economics[
        economics[
            "recommended_action"
        ].isin(
            [
                "payment_recovery",
                "checkout_recovery",
                "cart_recovery",
            ]
        )
    ]

    print(
        f"Eligible interventions: {len(eligible):,}"
    )

    print(
        f"Capacity limit: {DEFAULT_INTERVENTION_CAPACITY:,}"
    )

    portfolio = (
        optimize_intervention_portfolio(
            economics
        )
    )

    save_intervention_portfolio(
        portfolio
    )

    print()
    print(
        "2. SELECTED INTERVENTION PORTFOLIO"
    )

    print(
        f"Selected sessions: {len(portfolio):,}"
    )

    print()
    print(
        "3. PORTFOLIO ACTION DISTRIBUTION"
    )

    action_distribution = (
        portfolio.groupby(
            "recommended_action",
            as_index=False,
        )
        .agg(
            sessions=(
                "session_id",
                "count",
            ),
            expected_net_value=(
                "expected_net_value",
                "sum",
            ),
        )
        .sort_values(
            "expected_net_value",
            ascending=False,
        )
    )

    print(
        action_distribution
        .round(2)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "4. PORTFOLIO VALUE SUMMARY"
    )

    total_value = portfolio[
        "expected_net_value"
    ].sum()

    average_value = portfolio[
        "expected_net_value"
    ].mean()

    print(
        f"Total expected net value: "
        f"{total_value:.2f}"
    )

    print(
        f"Average expected net value: "
        f"{average_value:.2f}"
    )

    print()
    print(
        "5. TOP 10 PRIORITY INTERVENTIONS"
    )

    print(
        portfolio[
            [
                "portfolio_rank",
                "session_id",
                "recommended_action",
                "churn_risk_score",
                "cart_value",
                "expected_net_value",
                "business_priority_score",
            ]
        ]
        .head(10)
        .round(2)
        .to_string(
            index=False
        )
    )

    print()
    print(
        "INTERVENTION PORTFOLIO "
        "GENERATION COMPLETE"
    )


if __name__ == "__main__":
    main()