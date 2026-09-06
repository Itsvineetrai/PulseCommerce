"""Validate PulseCommerce churn risk scores."""

from __future__ import annotations

from pathlib import Path

import duckdb


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)

VALID_RISK_BANDS = (
    "low",
    "medium",
    "high",
    "critical",
)


def fetch_scalar(
    connection: duckdb.DuckDBPyConnection,
    query: str,
) -> int | float:
    """Execute a query and return its first scalar value."""

    return connection.execute(
        query
    ).fetchone()[0]


def main() -> None:
    """Validate the churn risk scoring output."""

    print(
        "PulseCommerce Churn Risk Score Validation"
    )

    print("-" * 60)

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        # -------------------------------------------------
        # 1. ROW AND SESSION RECONCILIATION
        # -------------------------------------------------

        print()
        print(
            "1. ROW AND SESSION RECONCILIATION"
        )

        reconciliation = connection.execute(
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM analytics_churn_feature_dataset
                ) AS feature_dataset_rows,
                (
                    SELECT COUNT(*)
                    FROM analytics_churn_risk_scores
                ) AS scored_rows,
                (
                    SELECT COUNT(DISTINCT session_id)
                    FROM analytics_churn_risk_scores
                ) AS distinct_scored_sessions
            """
        ).fetchdf()

        print(
            reconciliation.to_string(
                index=False
            )
        )

        # -------------------------------------------------
        # 2. DUPLICATE SESSION CHECK
        # -------------------------------------------------

        print()
        print(
            "2. DUPLICATE SESSION CHECK"
        )

        duplicate_sessions = fetch_scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    session_id
                FROM analytics_churn_risk_scores
                GROUP BY session_id
                HAVING COUNT(*) > 1
            )
            """,
        )

        print(
            f"Duplicate sessions: "
            f"{duplicate_sessions}"
        )

        # -------------------------------------------------
        # 3. NULL CHECK
        # -------------------------------------------------

        print()
        print(
            "3. RISK SCORE COMPLETENESS"
        )

        missing_scores = fetch_scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM analytics_churn_risk_scores
            WHERE
                churn_probability IS NULL
                OR churn_risk_score IS NULL
                OR risk_band IS NULL
            """,
        )

        print(
            f"Missing risk score values: "
            f"{missing_scores}"
        )

        # -------------------------------------------------
        # 4. SCORE RANGE CHECK
        # -------------------------------------------------

        print()
        print(
            "4. RISK SCORE RANGE"
        )

        score_range = connection.execute(
            """
            SELECT
                MIN(churn_risk_score)
                    AS minimum_risk_score,
                MAX(churn_risk_score)
                    AS maximum_risk_score,
                COUNT(*) FILTER (
                    WHERE
                        churn_risk_score < 0
                        OR churn_risk_score > 100
                )
                    AS out_of_range_scores
            FROM analytics_churn_risk_scores
            """
        ).fetchdf()

        print(
            score_range
            .round(4)
            .to_string(
                index=False
            )
        )

        # -------------------------------------------------
        # 5. RISK BAND CONTRACT
        # -------------------------------------------------

        print()
        print(
            "5. RISK BAND CONTRACT"
        )

        invalid_risk_bands = connection.execute(
            """
            SELECT
                risk_band,
                COUNT(*) AS sessions
            FROM analytics_churn_risk_scores
            WHERE risk_band NOT IN (
                'low',
                'medium',
                'high',
                'critical'
            )
            GROUP BY risk_band
            """
        ).fetchdf()

        invalid_band_count = int(
            invalid_risk_bands[
                "sessions"
            ].sum()
        ) if not invalid_risk_bands.empty else 0

        print(
            f"Invalid risk band rows: "
            f"{invalid_band_count}"
        )

        # -------------------------------------------------
        # 6. RISK BAND DISTRIBUTION
        # -------------------------------------------------

        print()
        print(
            "6. RISK BAND DISTRIBUTION"
        )

        distribution = connection.execute(
            """
            SELECT
                risk_band,
                COUNT(*) AS sessions,
                ROUND(
                    COUNT(*) * 100.0
                    / SUM(COUNT(*)) OVER (),
                    2
                ) AS percentage
            FROM analytics_churn_risk_scores
            GROUP BY risk_band
            ORDER BY
                CASE risk_band
                    WHEN 'low' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'high' THEN 3
                    WHEN 'critical' THEN 4
                END
            """
        ).fetchdf()

        print(
            distribution.to_string(
                index=False
            )
        )

        # -------------------------------------------------
        # 7. FEATURE DATASET RECONCILIATION
        # -------------------------------------------------

        print()
        print(
            "7. FEATURE DATASET RECONCILIATION"
        )

        missing_sessions = fetch_scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM analytics_churn_feature_dataset AS features
            LEFT JOIN analytics_churn_risk_scores AS scores
                ON features.session_id = scores.session_id
            WHERE scores.session_id IS NULL
            """,
        )

        unexpected_sessions = fetch_scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM analytics_churn_risk_scores AS scores
            LEFT JOIN analytics_churn_feature_dataset AS features
                ON scores.session_id = features.session_id
            WHERE features.session_id IS NULL
            """,
        )

        print(
            f"Feature sessions missing scores: "
            f"{missing_sessions}"
        )

        print(
            f"Unexpected scored sessions: "
            f"{unexpected_sessions}"
        )

        # -------------------------------------------------
        # FINAL RESULT
        # -------------------------------------------------

        validation_failed = any(
            [
                reconciliation.loc[
                    0,
                    "feature_dataset_rows",
                ]
                != reconciliation.loc[
                    0,
                    "scored_rows",
                ],
                reconciliation.loc[
                    0,
                    "scored_rows",
                ]
                != reconciliation.loc[
                    0,
                    "distinct_scored_sessions",
                ],
                duplicate_sessions != 0,
                missing_scores != 0,
                int(
                    score_range.loc[
                        0,
                        "out_of_range_scores",
                    ]
                )
                != 0,
                invalid_band_count != 0,
                missing_sessions != 0,
                unexpected_sessions != 0,
            ]
        )

        print()
        print(
            "8. FINAL VALIDATION"
        )

        if validation_failed:
            print(
                "PHASE 5 RISK SCORE VALIDATION FAILED"
            )

            raise SystemExit(
                1
            )

        print(
            "PHASE 5 RISK SCORE VALIDATION PASSED"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()