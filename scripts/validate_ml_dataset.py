"""Validate the PulseCommerce ML training dataset."""

from __future__ import annotations

from pathlib import Path

import duckdb


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


def main() -> None:
    """Validate feature integrity before model training."""

    print("PulseCommerce ML Dataset Validation")
    print("-" * 60)

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        # -----------------------------------------------------------
        # 1. Row and session integrity
        # -----------------------------------------------------------

        print()
        print("1. ROW AND SESSION INTEGRITY")

        integrity = connection.execute(
            """
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT session_id)
                    AS distinct_sessions,
                COUNT(*) -
                COUNT(DISTINCT session_id)
                    AS duplicate_sessions
            FROM analytics_churn_feature_dataset
            """
        ).fetchdf()

        print(
            integrity.to_string(
                index=False
            )
        )

        duplicate_sessions = int(
            integrity.iloc[0]["duplicate_sessions"]
        )

        if duplicate_sessions != 0:
            raise ValueError(
                "Duplicate sessions found."
            )

        # -----------------------------------------------------------
        # 2. Label integrity
        # -----------------------------------------------------------

        print()
        print("2. LABEL INTEGRITY")

        invalid_labels = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_churn_feature_dataset
            WHERE churned NOT IN (0, 1)
               OR churned IS NULL
            """
        ).fetchone()[0]

        print(
            f"Invalid churn labels: "
            f"{invalid_labels}"
        )

        if invalid_labels != 0:
            raise ValueError(
                "Invalid churn labels found."
            )

        # -----------------------------------------------------------
        # 3. Label and outcome consistency
        # -----------------------------------------------------------

        print()
        print("3. LABEL / OUTCOME CONSISTENCY")

        inconsistent_labels = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_churn_feature_dataset
            WHERE
                (
                    purchased = 1
                    AND churned != 0
                )
                OR
                (
                    purchased = 0
                    AND churned != 1
                )
            """
        ).fetchone()[0]

        print(
            "Inconsistent outcome labels: "
            f"{inconsistent_labels}"
        )

        if inconsistent_labels != 0:
            raise ValueError(
                "Purchased/churned labels "
                "are inconsistent."
            )

        # -----------------------------------------------------------
        # 4. Feature and leakage check
        # -----------------------------------------------------------

        print()
        print("4. FEATURE AND LEAKAGE CHECK")

        columns = connection.execute(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name =
                'analytics_churn_feature_dataset'
            ORDER BY ordinal_position
            """
        ).fetchall()

        column_names = [
            row[0]
            for row in columns
        ]

        forbidden_columns = {
            "purchased_1",
            "purchase_timestamp",
            "session_end_timestamp",
            "future_purchase",
        }

        detected_forbidden_columns = [
            column
            for column in column_names
            if column in forbidden_columns
        ]

        print(
            "Forbidden feature columns found: "
            f"{len(detected_forbidden_columns)}"
        )

        if detected_forbidden_columns:
            print(
                "Columns: "
                + ", ".join(
                    detected_forbidden_columns
                )
            )

            raise ValueError(
                "Duplicate or future-information "
                "columns found in ML dataset."
            )

        # -----------------------------------------------------------
        # 5. Outcome column contract
        # -----------------------------------------------------------

        print()
        print("5. OUTCOME COLUMN CONTRACT")

        expected_outcome_columns = {
            "purchased",
            "churned",
        }

        actual_outcome_columns = {
            column
            for column in column_names
            if column.startswith("purchased")
            or column.startswith("churned")
        }

        print(
            "Outcome columns: "
            + ", ".join(
                sorted(actual_outcome_columns)
            )
        )

        if (
            actual_outcome_columns
            != expected_outcome_columns
        ):
            raise ValueError(
                "Unexpected outcome columns found "
                "in ML dataset."
            )

        # -----------------------------------------------------------
        # 6. Required feature contract
        # -----------------------------------------------------------

        print()
        print("6. REQUIRED FEATURE CONTRACT")

        required_columns = {
            "user_id",
            "session_id",
            "observation_timestamp",
            "total_actions_so_far",
            "unique_event_types",
            "product_views",
            "add_to_cart_actions",
            "cart_views",
            "checkout_starts",
            "payment_attempts",
            "payment_errors",
            "has_cart",
            "reached_checkout",
            "observed_session_duration_minutes",
            "device_type",
            "traffic_source",
            "purchased",
            "churned",
        }

        missing_required_columns = (
            required_columns
            - set(column_names)
        )

        print(
            "Missing required columns: "
            f"{len(missing_required_columns)}"
        )

        if missing_required_columns:
            print(
                "Columns: "
                + ", ".join(
                    sorted(
                        missing_required_columns
                    )
                )
            )

            raise ValueError(
                "Required ML dataset columns "
                "are missing."
            )

        # -----------------------------------------------------------
        # 7. Final status
        # -----------------------------------------------------------

        print()
        print("7. ML DATASET READY")

        print()
        print("PHASE 5 FEATURE VALIDATION PASSED")

    finally:
        connection.close()


if __name__ == "__main__":
    main()