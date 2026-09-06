"""Build the PulseCommerce churn feature dataset."""

from __future__ import annotations

from pathlib import Path

import duckdb

from pulsecommerce.ml.feature_service import (
    build_churn_feature_dataset,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


def main() -> None:
    """Build and summarize the churn feature dataset."""

    print("PulseCommerce Churn Feature Dataset")
    print("-" * 60)

    build_churn_feature_dataset()

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        summary = connection.execute(
            """
            SELECT
                COUNT(*) AS total_sessions,
                COUNT(DISTINCT user_id) AS total_users,
                SUM(churned) AS churned_sessions,
                SUM(1 - churned) AS converted_sessions,
                ROUND(
                    100.0 * AVG(churned),
                    2
                ) AS churn_rate_pct
            FROM analytics_churn_feature_dataset
            """
        ).fetchdf()

        print(summary.to_string(index=False))

        print()
        print("CHURN DISTRIBUTION")

        distribution = connection.execute(
            """
            SELECT
                churned,
                COUNT(*) AS sessions,
                ROUND(
                    100.0
                    * COUNT(*)
                    / SUM(COUNT(*)) OVER (),
                    2
                ) AS percentage
            FROM analytics_churn_feature_dataset
            GROUP BY churned
            ORDER BY churned
            """
        ).fetchdf()

        print(distribution.to_string(index=False))

        print()
        print("FEATURE DATASET CREATED SUCCESSFULLY")

    finally:
        connection.close()


if __name__ == "__main__":
    main()