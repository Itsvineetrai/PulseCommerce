from __future__ import annotations

from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

WAREHOUSE_PATH = PROJECT_ROOT / "data" / "warehouse" / "pulsecommerce.duckdb"
CHURN_MODEL_PATH = PROJECT_ROOT / "artifacts" / "churn_model.joblib"

EXPECTED_SESSION_COUNT = 15_000
PORTFOLIO_CAPACITY = 500

REQUIRED_TABLES = [
    "events",
    "analytics_session_funnel",
    "analytics_funnel_metrics",
    "analytics_velocity_metrics",
    "analytics_experiment_population",
    "analytics_churn_feature_dataset",
    "analytics_churn_risk_scores",
    "analytics_intervention_candidates",
    "analytics_intervention_economics",
    "analytics_intervention_portfolio",
    "analytics_intervention_roi",
]


def check_required_table(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> None:
    exists = connection.execute(
        """
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_schema = 'main'
          AND table_name = ?
        """,
        [table_name],
    ).fetchone()[0]

    if exists != 1:
        raise RuntimeError(
            f"Required table is missing: {table_name}"
        )


def get_row_count(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> int:
    return connection.execute(
        f"SELECT COUNT(*) FROM {table_name}"
    ).fetchone()[0]


def get_duplicate_session_count(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
) -> int:
    return connection.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT session_id
            FROM {table_name}
            GROUP BY session_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]


def get_null_count(
    connection: duckdb.DuckDBPyConnection,
    table_name: str,
    column_name: str,
) -> int:
    return connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {table_name}
        WHERE {column_name} IS NULL
        """
    ).fetchone()[0]


def main() -> None:
    print("PulseCommerce Complete End-to-End Pipeline Validation")
    print("-" * 65)

    print("\n1. PROJECT ARTIFACT CHECK")

    if not WAREHOUSE_PATH.exists():
        raise FileNotFoundError(
            f"Warehouse database not found: {WAREHOUSE_PATH}"
        )

    if not CHURN_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Churn model artifact not found: {CHURN_MODEL_PATH}"
        )

    print("Warehouse artifact: PASSED")
    print("Churn model artifact: PASSED")

    connection = duckdb.connect(
        str(WAREHOUSE_PATH),
        read_only=True,
    )

    try:
        print("\n2. WAREHOUSE TABLE CHECK")

        for table_name in REQUIRED_TABLES:
            check_required_table(
                connection,
                table_name,
            )

        print(
            f"Required warehouse tables: {len(REQUIRED_TABLES)}"
        )
        print("Warehouse table validation: PASSED")

        print("\n3. CHURN FEATURE DATASET VALIDATION")

        churn_rows = get_row_count(
            connection,
            "analytics_churn_feature_dataset",
        )

        churn_duplicates = get_duplicate_session_count(
            connection,
            "analytics_churn_feature_dataset",
        )

        print(f"Churn dataset sessions: {churn_rows:,}")
        print(
            f"Duplicate churn sessions: {churn_duplicates:,}"
        )

        if churn_rows != EXPECTED_SESSION_COUNT:
            raise RuntimeError(
                f"Expected {EXPECTED_SESSION_COUNT:,} churn sessions "
                f"but found {churn_rows:,}."
            )

        if churn_duplicates != 0:
            raise RuntimeError(
                "Duplicate session IDs found in churn dataset."
            )

        print("Churn feature dataset: PASSED")

        print("\n4. CHURN RISK SCORE RECONCILIATION")

        risk_rows = get_row_count(
            connection,
            "analytics_churn_risk_scores",
        )

        risk_duplicates = get_duplicate_session_count(
            connection,
            "analytics_churn_risk_scores",
        )

        missing_risk_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_churn_feature_dataset AS features
            LEFT JOIN analytics_churn_risk_scores AS scores
                USING (session_id)
            WHERE scores.session_id IS NULL
            """
        ).fetchone()[0]

        unexpected_risk_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_churn_risk_scores AS scores
            LEFT JOIN analytics_churn_feature_dataset AS features
                USING (session_id)
            WHERE features.session_id IS NULL
            """
        ).fetchone()[0]

        print(f"Risk score sessions: {risk_rows:,}")
        print(
            f"Duplicate risk sessions: {risk_duplicates:,}"
        )
        print(
            f"Feature sessions missing scores: "
            f"{missing_risk_sessions:,}"
        )
        print(
            f"Unexpected scored sessions: "
            f"{unexpected_risk_sessions:,}"
        )

        if risk_rows != EXPECTED_SESSION_COUNT:
            raise RuntimeError(
                "Risk score row count does not match "
                "expected session count."
            )

        if risk_duplicates != 0:
            raise RuntimeError(
                "Duplicate session IDs found in risk scores."
            )

        if missing_risk_sessions != 0:
            raise RuntimeError(
                "Feature dataset contains sessions "
                "missing churn risk scores."
            )

        if unexpected_risk_sessions != 0:
            raise RuntimeError(
                "Risk score dataset contains unexpected sessions."
            )

        print("Churn risk reconciliation: PASSED")

        print("\n5. INTERVENTION CANDIDATE VALIDATION")

        candidate_rows = get_row_count(
            connection,
            "analytics_intervention_candidates",
        )

        candidate_duplicates = get_duplicate_session_count(
            connection,
            "analytics_intervention_candidates",
        )

        missing_candidate_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_candidates AS candidates
            LEFT JOIN analytics_churn_risk_scores AS scores
                USING (session_id)
            WHERE scores.session_id IS NULL
            """
        ).fetchone()[0]

        null_actions = get_null_count(
            connection,
            "analytics_intervention_candidates",
            "recommended_action",
        )

        print(f"Candidate sessions: {candidate_rows:,}")
        print(
            f"Duplicate candidate sessions: "
            f"{candidate_duplicates:,}"
        )
        print(
            f"Candidates missing risk scores: "
            f"{missing_candidate_sessions:,}"
        )
        print(
            f"Missing recommended actions: {null_actions:,}"
        )

        if candidate_rows != EXPECTED_SESSION_COUNT:
            raise RuntimeError(
                "Intervention candidate row count does not match "
                "expected session count."
            )

        if candidate_duplicates != 0:
            raise RuntimeError(
                "Duplicate session IDs found in intervention candidates."
            )

        if missing_candidate_sessions != 0:
            raise RuntimeError(
                "Intervention candidates contain sessions "
                "without risk scores."
            )

        if null_actions != 0:
            raise RuntimeError(
                "Intervention candidates contain missing actions."
            )

        print("Intervention candidates: PASSED")

        print("\n6. INTERVENTION ECONOMICS RECONCILIATION")

        economics_rows = get_row_count(
            connection,
            "analytics_intervention_economics",
        )

        economics_duplicates = get_duplicate_session_count(
            connection,
            "analytics_intervention_economics",
        )

        missing_economics_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_candidates AS candidates
            LEFT JOIN analytics_intervention_economics AS economics
                USING (session_id)
            WHERE economics.session_id IS NULL
            """
        ).fetchone()[0]

        print(f"Economics sessions: {economics_rows:,}")
        print(
            f"Duplicate economics sessions: "
            f"{economics_duplicates:,}"
        )
        print(
            f"Candidates missing economics: "
            f"{missing_economics_sessions:,}"
        )

        if economics_rows != EXPECTED_SESSION_COUNT:
            raise RuntimeError(
                "Intervention economics row count does not match "
                "expected session count."
            )

        if economics_duplicates != 0:
            raise RuntimeError(
                "Duplicate session IDs found in intervention economics."
            )

        if missing_economics_sessions != 0:
            raise RuntimeError(
                "Intervention candidates missing economics records."
            )

        print("Intervention economics: PASSED")

        print("\n7. INTERVENTION PORTFOLIO VALIDATION")

        portfolio_rows = get_row_count(
            connection,
            "analytics_intervention_portfolio",
        )

        portfolio_duplicates = get_duplicate_session_count(
            connection,
            "analytics_intervention_portfolio",
        )

        missing_portfolio_economics = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_portfolio AS portfolio
            LEFT JOIN analytics_intervention_economics AS economics
                USING (session_id)
            WHERE economics.session_id IS NULL
            """
        ).fetchone()[0]

        print(f"Portfolio sessions: {portfolio_rows:,}")
        print(
            f"Portfolio capacity limit: {PORTFOLIO_CAPACITY:,}"
        )
        print(
            f"Duplicate portfolio sessions: "
            f"{portfolio_duplicates:,}"
        )
        print(
            f"Portfolio sessions missing economics: "
            f"{missing_portfolio_economics:,}"
        )

        if portfolio_rows > PORTFOLIO_CAPACITY:
            raise RuntimeError(
                "Portfolio exceeds configured capacity."
            )

        if portfolio_duplicates != 0:
            raise RuntimeError(
                "Duplicate session IDs found in portfolio."
            )

        if missing_portfolio_economics != 0:
            raise RuntimeError(
                "Portfolio contains sessions "
                "without economics records."
            )

        print("Intervention portfolio: PASSED")

        print("\n8. ROI RECONCILIATION")

        roi_rows = get_row_count(
            connection,
            "analytics_intervention_roi",
        )

        roi_duplicates = get_duplicate_session_count(
            connection,
            "analytics_intervention_roi",
        )

        missing_roi_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_portfolio AS portfolio
            LEFT JOIN analytics_intervention_roi AS roi
                USING (session_id)
            WHERE roi.session_id IS NULL
            """
        ).fetchone()[0]

        unexpected_roi_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_roi AS roi
            LEFT JOIN analytics_intervention_portfolio AS portfolio
                USING (session_id)
            WHERE portfolio.session_id IS NULL
            """
        ).fetchone()[0]

        print(f"ROI sessions: {roi_rows:,}")
        print(
            f"Duplicate ROI sessions: {roi_duplicates:,}"
        )
        print(
            f"Portfolio sessions missing ROI: "
            f"{missing_roi_sessions:,}"
        )
        print(
            f"Unexpected ROI sessions: "
            f"{unexpected_roi_sessions:,}"
        )

        if roi_rows != portfolio_rows:
            raise RuntimeError(
                "ROI row count does not match portfolio row count."
            )

        if roi_duplicates != 0:
            raise RuntimeError(
                "Duplicate session IDs found in ROI dataset."
            )

        if missing_roi_sessions != 0:
            raise RuntimeError(
                "Portfolio sessions missing ROI records."
            )

        if unexpected_roi_sessions != 0:
            raise RuntimeError(
                "ROI dataset contains sessions "
                "outside the selected portfolio."
            )

        print("ROI reconciliation: PASSED")

        print("\n9. FINAL PIPELINE CONTRACT")

        print(
            f"Source sessions: {EXPECTED_SESSION_COUNT:,}"
        )
        print(
            f"Portfolio sessions: {portfolio_rows:,}"
        )
        print(
            f"ROI sessions: {roi_rows:,}"
        )

        print("\nCOMPLETE END-TO-END PIPELINE VALIDATION PASSED")

    finally:
        connection.close()


if __name__ == "__main__":
    main()