"""Validate PulseCommerce intervention candidates."""

from __future__ import annotations

from pathlib import Path

import duckdb


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


VALID_ACTIONS = {
    "payment_recovery",
    "checkout_recovery",
    "cart_recovery",
    "monitor",
    "no_action",
}


ACTION_PRIORITY_MAPPING = {
    "payment_recovery": "critical",
    "checkout_recovery": "high",
    "cart_recovery": "high",
    "monitor": "medium",
    "no_action": "low",
}


def fetch_scalar(
    connection: duckdb.DuckDBPyConnection,
    query: str,
) -> int:
    """Execute a scalar query."""

    return connection.execute(
        query
    ).fetchone()[0]


def main() -> None:
    """Validate intervention candidate output."""

    print(
        "PulseCommerce Intervention Candidate Validation"
    )

    print("-" * 60)

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        # ---------------------------------------------
        # 1. ROW RECONCILIATION
        # ---------------------------------------------

        print()
        print(
            "1. ROW RECONCILIATION"
        )

        reconciliation = connection.execute(
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM analytics_churn_risk_scores
                ) AS scored_sessions,
                (
                    SELECT COUNT(*)
                    FROM analytics_intervention_candidates
                ) AS intervention_sessions,
                (
                    SELECT COUNT(DISTINCT session_id)
                    FROM analytics_intervention_candidates
                ) AS distinct_intervention_sessions
            """
        ).fetchdf()

        print(
            reconciliation.to_string(
                index=False
            )
        )

        # ---------------------------------------------
        # 2. DUPLICATE SESSION CHECK
        # ---------------------------------------------

        print()
        print(
            "2. DUPLICATE SESSION CHECK"
        )

        duplicate_sessions = fetch_scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM (
                SELECT session_id
                FROM analytics_intervention_candidates
                GROUP BY session_id
                HAVING COUNT(*) > 1
            )
            """,
        )

        print(
            f"Duplicate sessions: "
            f"{duplicate_sessions}"
        )

        # ---------------------------------------------
        # 3. COMPLETENESS CHECK
        # ---------------------------------------------

        print()
        print(
            "3. INTERVENTION COMPLETENESS"
        )

        missing_values = fetch_scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM analytics_intervention_candidates
            WHERE
                recommended_action IS NULL
                OR intervention_priority IS NULL
            """,
        )

        print(
            f"Missing intervention values: "
            f"{missing_values}"
        )

        # ---------------------------------------------
        # 4. ACTION CONTRACT
        # ---------------------------------------------

        print()
        print(
            "4. ACTION CONTRACT"
        )

        invalid_actions = connection.execute(
            """
            SELECT
                recommended_action,
                COUNT(*) AS sessions
            FROM analytics_intervention_candidates
            WHERE recommended_action NOT IN (
                'payment_recovery',
                'checkout_recovery',
                'cart_recovery',
                'monitor',
                'no_action'
            )
            GROUP BY recommended_action
            """
        ).fetchdf()

        invalid_action_count = (
            int(
                invalid_actions[
                    "sessions"
                ].sum()
            )
            if not invalid_actions.empty
            else 0
        )

        print(
            f"Invalid action rows: "
            f"{invalid_action_count}"
        )

        # ---------------------------------------------
        # 5. PRIORITY CONTRACT
        # ---------------------------------------------

        print()
        print(
            "5. PRIORITY CONTRACT"
        )

        invalid_priorities = connection.execute(
            """
            SELECT
                intervention_priority,
                COUNT(*) AS sessions
            FROM analytics_intervention_candidates
            WHERE intervention_priority NOT IN (
                'critical',
                'high',
                'medium',
                'low'
            )
            GROUP BY intervention_priority
            """
        ).fetchdf()

        invalid_priority_count = (
            int(
                invalid_priorities[
                    "sessions"
                ].sum()
            )
            if not invalid_priorities.empty
            else 0
        )

        print(
            f"Invalid priority rows: "
            f"{invalid_priority_count}"
        )

        # ---------------------------------------------
        # 6. ACTION / PRIORITY CONSISTENCY
        # ---------------------------------------------

        print()
        print(
            "6. ACTION / PRIORITY CONSISTENCY"
        )

        inconsistent_actions = fetch_scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM analytics_intervention_candidates
            WHERE
                (recommended_action = 'payment_recovery'
                    AND intervention_priority != 'critical')
                OR
                (recommended_action = 'checkout_recovery'
                    AND intervention_priority != 'high')
                OR
                (recommended_action = 'cart_recovery'
                    AND intervention_priority != 'high')
                OR
                (recommended_action = 'monitor'
                    AND intervention_priority != 'medium')
                OR
                (recommended_action = 'no_action'
                    AND intervention_priority != 'low')
            """,
        )

        print(
            f"Inconsistent action/priority rows: "
            f"{inconsistent_actions}"
        )

        # ---------------------------------------------
        # 7. SESSION RECONCILIATION
        # ---------------------------------------------

        print()
        print(
            "7. SESSION RECONCILIATION"
        )

        missing_interventions = fetch_scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM analytics_churn_risk_scores AS scores
            LEFT JOIN analytics_intervention_candidates AS candidates
                ON scores.session_id = candidates.session_id
            WHERE candidates.session_id IS NULL
            """,
        )

        unexpected_interventions = fetch_scalar(
            connection,
            """
            SELECT COUNT(*)
            FROM analytics_intervention_candidates AS candidates
            LEFT JOIN analytics_churn_risk_scores AS scores
                ON candidates.session_id = scores.session_id
            WHERE scores.session_id IS NULL
            """,
        )

        print(
            f"Scored sessions missing interventions: "
            f"{missing_interventions}"
        )

        print(
            f"Unexpected intervention sessions: "
            f"{unexpected_interventions}"
        )

        # ---------------------------------------------
        # FINAL RESULT
        # ---------------------------------------------

        validation_failed = any(
            [
                reconciliation.loc[
                    0,
                    "scored_sessions",
                ]
                != reconciliation.loc[
                    0,
                    "intervention_sessions",
                ],
                reconciliation.loc[
                    0,
                    "intervention_sessions",
                ]
                != reconciliation.loc[
                    0,
                    "distinct_intervention_sessions",
                ],
                duplicate_sessions != 0,
                missing_values != 0,
                invalid_action_count != 0,
                invalid_priority_count != 0,
                inconsistent_actions != 0,
                missing_interventions != 0,
                unexpected_interventions != 0,
            ]
        )

        print()
        print(
            "8. FINAL VALIDATION"
        )

        if validation_failed:
            print(
                "PHASE 6 INTERVENTION VALIDATION FAILED"
            )

            raise SystemExit(1)

        print(
            "PHASE 6 BATCH 1 VALIDATION PASSED"
        )

    finally:
        connection.close()


if __name__ == "__main__":
    main()