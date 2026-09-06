"""Generate PulseCommerce intervention candidates."""

from __future__ import annotations

from pathlib import Path

import duckdb

from pulsecommerce.intervention.intervention_service import (
    generate_intervention_candidates,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


def load_intervention_dataset():
    """Load risk scores with behavioral context."""

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        return connection.execute(
            """
            SELECT
                scores.user_id,
                scores.session_id,
                scores.observation_timestamp,
                scores.churn_probability,
                scores.churn_risk_score,
                scores.risk_band,
                scores.has_cart,
                scores.reached_checkout,
                features.payment_errors
            FROM analytics_churn_risk_scores AS scores
            INNER JOIN analytics_churn_feature_dataset AS features
                ON scores.session_id = features.session_id
            """
        ).fetchdf()

    finally:
        connection.close()


def save_intervention_candidates(
    candidates,
) -> None:
    """Persist intervention candidates."""

    connection = duckdb.connect(
        str(DATABASE_PATH)
    )

    try:
        connection.register(
            "intervention_candidates_df",
            candidates,
        )

        connection.execute(
            """
            CREATE OR REPLACE TABLE
            analytics_intervention_candidates AS
            SELECT *
            FROM intervention_candidates_df
            """
        )

        connection.unregister(
            "intervention_candidates_df"
        )

    finally:
        connection.close()


def main() -> None:
    """Generate and persist intervention candidates."""

    print(
        "PulseCommerce Intervention Engine"
    )

    print("-" * 60)

    dataset = (
        load_intervention_dataset()
    )

    print()
    print(
        "1. LOADED SCORED SESSIONS"
    )

    print(
        f"Sessions: {len(dataset):,}"
    )

    candidates = (
        generate_intervention_candidates(
            dataset
        )
    )

    save_intervention_candidates(
        candidates
    )

    print()
    print(
        "2. INTERVENTION ACTION DISTRIBUTION"
    )

    action_distribution = (
        candidates[
            "recommended_action"
        ]
        .value_counts()
        .rename_axis(
            "recommended_action"
        )
        .reset_index(
            name="sessions"
        )
    )

    print(
        action_distribution.to_string(
            index=False
        )
    )

    print()
    print(
        "3. INTERVENTION PRIORITY DISTRIBUTION"
    )

    priority_distribution = (
        candidates[
            "intervention_priority"
        ]
        .value_counts()
        .rename_axis(
            "intervention_priority"
        )
        .reset_index(
            name="sessions"
        )
    )

    print(
        priority_distribution.to_string(
            index=False
        )
    )

    print()
    print(
        "INTERVENTION CANDIDATE GENERATION COMPLETE"
    )


if __name__ == "__main__":
    main()