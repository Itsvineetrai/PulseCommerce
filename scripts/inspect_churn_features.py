"""Inspect the PulseCommerce churn feature dataset."""

from __future__ import annotations

from pathlib import Path

import duckdb


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


def main() -> None:
    """Inspect churn features before model training."""

    print("PulseCommerce ML Feature Inspection")
    print("-" * 60)

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        print()
        print("1. FEATURE DATASET SCHEMA")

        schema = connection.execute(
            """
            DESCRIBE analytics_churn_feature_dataset
            """
        ).fetchdf()

        print(schema.to_string(index=False))

        print()
        print("2. MISSING VALUE CHECK")

        columns = connection.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name =
                'analytics_churn_feature_dataset'
            ORDER BY ordinal_position
            """
        ).fetchall()

        missing_expressions = []

        for (column_name,) in columns:
            missing_expressions.append(
                f"""
                SUM(
                    CASE
                        WHEN "{column_name}" IS NULL
                        THEN 1
                        ELSE 0
                    END
                ) AS "{column_name}"
                """
            )

        missing_query = (
            "SELECT\n"
            + ",\n".join(
                missing_expressions
            )
            + "\nFROM analytics_churn_feature_dataset"
        )

        missing_values = connection.execute(
            missing_query
        ).fetchdf()

        print(
            missing_values.to_string(
                index=False
            )
        )

        print()
        print("3. LABEL DISTRIBUTION")

        label_distribution = connection.execute(
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

        print(
            label_distribution.to_string(
                index=False
            )
        )

        print()
        print("4. NUMERIC FEATURE SUMMARY")

        numeric_summary = connection.execute(
            """
            SELECT
                ROUND(
                    AVG(total_actions_so_far),
                    2
                ) AS avg_total_actions,

                MIN(total_actions_so_far)
                    AS min_total_actions,

                MAX(total_actions_so_far)
                    AS max_total_actions,

                ROUND(
                    AVG(unique_event_types),
                    2
                ) AS avg_unique_event_types,

                ROUND(
                    AVG(product_views),
                    2
                ) AS avg_product_views,

                ROUND(
                    AVG(add_to_cart_actions),
                    2
                ) AS avg_add_to_cart_actions,

                ROUND(
                    AVG(cart_views),
                    2
                ) AS avg_cart_views,

                ROUND(
                    AVG(checkout_starts),
                    2
                ) AS avg_checkout_starts,

                ROUND(
                    AVG(payment_attempts),
                    2
                ) AS avg_payment_attempts,

                ROUND(
                    AVG(payment_errors),
                    2
                ) AS avg_payment_errors,

                ROUND(
                    AVG(
                        observed_session_duration_minutes
                    ),
                    2
                ) AS avg_observed_duration_minutes

            FROM analytics_churn_feature_dataset
            """
        ).fetchdf()

        print(
            numeric_summary.to_string(
                index=False
            )
        )

        print()
        print("5. CATEGORICAL FEATURE DISTRIBUTION")

        categorical_distribution = connection.execute(
            """
            SELECT
                device_type,
                traffic_source,
                COUNT(*) AS sessions
            FROM analytics_churn_feature_dataset
            GROUP BY
                device_type,
                traffic_source
            ORDER BY sessions DESC
            """
        ).fetchdf()

        print(
            categorical_distribution.to_string(
                index=False
            )
        )

        print()
        print("FEATURE INSPECTION COMPLETE")

    finally:
        connection.close()


if __name__ == "__main__":
    main()