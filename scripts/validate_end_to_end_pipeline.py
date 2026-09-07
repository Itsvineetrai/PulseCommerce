"""Validate the complete PulseCommerce end-to-end pipeline."""

from pathlib import Path

import duckdb


PROJECT_ROOT = Path(__file__).resolve().parents[1]

WAREHOUSE_PATH = (
    PROJECT_ROOT
    / "data"
    / "warehouse"
    / "pulsecommerce.duckdb"
)

CHURN_MODEL_PATH = (
    PROJECT_ROOT
    / "artifacts"
    / "churn_model.joblib"
)


REQUIRED_TABLES = {
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
}


def require(condition: bool, message: str) -> None:
    """Raise an error when a validation contract fails."""

    if not condition:
        raise ValueError(message)


def main() -> None:
    """Run complete end-to-end pipeline validation."""

    print("PulseCommerce End-to-End Pipeline Validation")
    print("-" * 60)

    # ---------------------------------------------------------
    # 1. PROJECT ARTIFACT CHECK
    # ---------------------------------------------------------

    print("\n1. PROJECT ARTIFACT CHECK")

    require(
        WAREHOUSE_PATH.exists(),
        f"Warehouse artifact not found: {WAREHOUSE_PATH}",
    )

    print("Warehouse artifact: PASSED")

    require(
        CHURN_MODEL_PATH.exists(),
        f"Churn model artifact not found: {CHURN_MODEL_PATH}",
    )

    print("Churn model artifact: PASSED")

    # ---------------------------------------------------------
    # DATABASE CONNECTION
    # ---------------------------------------------------------

    connection = duckdb.connect(
        str(WAREHOUSE_PATH),
        read_only=True,
    )

    try:
        # -----------------------------------------------------
        # 2. WAREHOUSE TABLE CHECK
        # -----------------------------------------------------

        print("\n2. WAREHOUSE TABLE CHECK")

        available_tables = {
            row[0]
            for row in connection.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'main'
                """
            ).fetchall()
        }

        missing_tables = REQUIRED_TABLES - available_tables

        require(
            not missing_tables,
            (
                "Missing required warehouse tables: "
                f"{sorted(missing_tables)}"
            ),
        )

        print(
            f"Required warehouse tables: {len(REQUIRED_TABLES)}"
        )

        print("Warehouse table validation: PASSED")

        # -----------------------------------------------------
        # 3. CHURN FEATURE DATASET VALIDATION
        # -----------------------------------------------------

        print("\n3. CHURN FEATURE DATASET VALIDATION")

        churn_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_churn_feature_dataset
            """
        ).fetchone()[0]

        duplicate_churn_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    session_id
                FROM analytics_churn_feature_dataset
                GROUP BY session_id
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        require(
            churn_sessions > 0,
            "Churn feature dataset contains no sessions.",
        )

        require(
            duplicate_churn_sessions == 0,
            (
                "Duplicate churn feature sessions found: "
                f"{duplicate_churn_sessions}"
            ),
        )

        print(
            f"Churn dataset sessions: {churn_sessions:,}"
        )

        print(
            f"Duplicate churn sessions: "
            f"{duplicate_churn_sessions:,}"
        )

        print("Churn feature dataset: PASSED")

        # -----------------------------------------------------
        # 4. CHURN RISK SCORE RECONCILIATION
        # -----------------------------------------------------

        print("\n4. CHURN RISK SCORE RECONCILIATION")

        risk_score_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_churn_risk_scores
            """
        ).fetchone()[0]

        duplicate_risk_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    session_id
                FROM analytics_churn_risk_scores
                GROUP BY session_id
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        feature_sessions_missing_scores = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_churn_feature_dataset AS features
            LEFT JOIN analytics_churn_risk_scores AS scores
                USING (session_id)
            WHERE scores.session_id IS NULL
            """
        ).fetchone()[0]

        unexpected_scored_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_churn_risk_scores AS scores
            LEFT JOIN analytics_churn_feature_dataset AS features
                USING (session_id)
            WHERE features.session_id IS NULL
            """
        ).fetchone()[0]

        require(
            risk_score_sessions == churn_sessions,
            (
                "Risk score session count does not match "
                "churn feature dataset."
            ),
        )

        require(
            duplicate_risk_sessions == 0,
            (
                "Duplicate risk score sessions found: "
                f"{duplicate_risk_sessions}"
            ),
        )

        require(
            feature_sessions_missing_scores == 0,
            (
                "Feature sessions missing risk scores: "
                f"{feature_sessions_missing_scores}"
            ),
        )

        require(
            unexpected_scored_sessions == 0,
            (
                "Unexpected scored sessions: "
                f"{unexpected_scored_sessions}"
            ),
        )

        print(
            f"Risk score sessions: {risk_score_sessions:,}"
        )

        print(
            f"Duplicate risk sessions: "
            f"{duplicate_risk_sessions:,}"
        )

        print(
            f"Feature sessions missing scores: "
            f"{feature_sessions_missing_scores:,}"
        )

        print(
            f"Unexpected scored sessions: "
            f"{unexpected_scored_sessions:,}"
        )

        print("Churn risk reconciliation: PASSED")

        # -----------------------------------------------------
        # 5. INTERVENTION CANDIDATE VALIDATION
        # -----------------------------------------------------

        print("\n5. INTERVENTION CANDIDATE VALIDATION")

        candidate_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_candidates
            """
        ).fetchone()[0]

        duplicate_candidate_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    session_id
                FROM analytics_intervention_candidates
                GROUP BY session_id
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        candidates_missing_risk_scores = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_candidates AS candidates
            LEFT JOIN analytics_churn_risk_scores AS scores
                USING (session_id)
            WHERE scores.session_id IS NULL
            """
        ).fetchone()[0]

        missing_recommended_actions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_candidates
            WHERE recommended_action IS NULL
               OR TRIM(recommended_action) = ''
            """
        ).fetchone()[0]

        require(
            candidate_sessions == risk_score_sessions,
            (
                "Candidate session count does not match "
                "risk score session count."
            ),
        )

        require(
            duplicate_candidate_sessions == 0,
            (
                "Duplicate candidate sessions found: "
                f"{duplicate_candidate_sessions}"
            ),
        )

        require(
            candidates_missing_risk_scores == 0,
            (
                "Candidates missing risk scores: "
                f"{candidates_missing_risk_scores}"
            ),
        )

        require(
            missing_recommended_actions == 0,
            (
                "Missing recommended actions: "
                f"{missing_recommended_actions}"
            ),
        )

        print(
            f"Candidate sessions: {candidate_sessions:,}"
        )

        print(
            f"Duplicate candidate sessions: "
            f"{duplicate_candidate_sessions:,}"
        )

        print(
            f"Candidates missing risk scores: "
            f"{candidates_missing_risk_scores:,}"
        )

        print(
            f"Missing recommended actions: "
            f"{missing_recommended_actions:,}"
        )

        print("Intervention candidates: PASSED")

        # -----------------------------------------------------
        # 6. INTERVENTION ECONOMICS RECONCILIATION
        # -----------------------------------------------------

        print("\n6. INTERVENTION ECONOMICS RECONCILIATION")

        economics_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_economics
            """
        ).fetchone()[0]

        duplicate_economics_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    session_id
                FROM analytics_intervention_economics
                GROUP BY session_id
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        candidates_missing_economics = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_candidates AS candidates
            LEFT JOIN analytics_intervention_economics AS economics
                USING (session_id)
            WHERE economics.session_id IS NULL
            """
        ).fetchone()[0]

        require(
            economics_sessions == candidate_sessions,
            (
                "Economics session count does not match "
                "candidate session count."
            ),
        )

        require(
            duplicate_economics_sessions == 0,
            (
                "Duplicate economics sessions found: "
                f"{duplicate_economics_sessions}"
            ),
        )

        require(
            candidates_missing_economics == 0,
            (
                "Candidates missing economics: "
                f"{candidates_missing_economics}"
            ),
        )

        print(
            f"Economics sessions: {economics_sessions:,}"
        )

        print(
            f"Duplicate economics sessions: "
            f"{duplicate_economics_sessions:,}"
        )

        print(
            f"Candidates missing economics: "
            f"{candidates_missing_economics:,}"
        )

        print("Intervention economics: PASSED")

        # -----------------------------------------------------
        # 7. INTERVENTION PORTFOLIO VALIDATION
        # -----------------------------------------------------

        print("\n7. INTERVENTION PORTFOLIO VALIDATION")

        portfolio_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_portfolio
            """
        ).fetchone()[0]

        duplicate_portfolio_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    session_id
                FROM analytics_intervention_portfolio
                GROUP BY session_id
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        portfolio_missing_economics = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_portfolio AS portfolio
            LEFT JOIN analytics_intervention_economics AS economics
                USING (session_id)
            WHERE economics.session_id IS NULL
            """
        ).fetchone()[0]

        portfolio_capacity_limit = 500

        require(
            portfolio_sessions <= portfolio_capacity_limit,
            (
                "Portfolio exceeds capacity limit: "
                f"{portfolio_sessions} > {portfolio_capacity_limit}"
            ),
        )

        require(
            duplicate_portfolio_sessions == 0,
            (
                "Duplicate portfolio sessions found: "
                f"{duplicate_portfolio_sessions}"
            ),
        )

        require(
            portfolio_missing_economics == 0,
            (
                "Portfolio sessions missing economics: "
                f"{portfolio_missing_economics}"
            ),
        )

        print(
            f"Portfolio sessions: {portfolio_sessions:,}"
        )

        print(
            f"Portfolio capacity limit: "
            f"{portfolio_capacity_limit:,}"
        )

        print(
            f"Duplicate portfolio sessions: "
            f"{duplicate_portfolio_sessions:,}"
        )

        print(
            f"Portfolio sessions missing economics: "
            f"{portfolio_missing_economics:,}"
        )

        print("Intervention portfolio: PASSED")

        # -----------------------------------------------------
        # 8. ROI RECONCILIATION
        # -----------------------------------------------------

        print("\n8. ROI RECONCILIATION")

        roi_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_roi
            """
        ).fetchone()[0]

        duplicate_roi_sessions = connection.execute(
            """
            SELECT COUNT(*)
            FROM (
                SELECT
                    session_id
                FROM analytics_intervention_roi
                GROUP BY session_id
                HAVING COUNT(*) > 1
            )
            """
        ).fetchone()[0]

        portfolio_missing_roi = connection.execute(
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

        require(
            roi_sessions == portfolio_sessions,
            (
                "ROI session count does not match "
                "portfolio session count."
            ),
        )

        require(
            duplicate_roi_sessions == 0,
            (
                "Duplicate ROI sessions found: "
                f"{duplicate_roi_sessions}"
            ),
        )

        require(
            portfolio_missing_roi == 0,
            (
                "Portfolio sessions missing ROI: "
                f"{portfolio_missing_roi}"
            ),
        )

        require(
            unexpected_roi_sessions == 0,
            (
                "Unexpected ROI sessions: "
                f"{unexpected_roi_sessions}"
            ),
        )

        print(
            f"ROI sessions: {roi_sessions:,}"
        )

        print(
            f"Duplicate ROI sessions: "
            f"{duplicate_roi_sessions:,}"
        )

        print(
            f"Portfolio sessions missing ROI: "
            f"{portfolio_missing_roi:,}"
        )

        print(
            f"Unexpected ROI sessions: "
            f"{unexpected_roi_sessions:,}"
        )

        print("ROI reconciliation: PASSED")

        # -----------------------------------------------------
        # 9. FINAL PIPELINE CONTRACT
        # -----------------------------------------------------

        print("\n9. FINAL PIPELINE CONTRACT")

        require(
            churn_sessions == risk_score_sessions,
            "Source and risk score session counts do not match.",
        )

        require(
            candidate_sessions == economics_sessions,
            "Candidate and economics session counts do not match.",
        )

        require(
            portfolio_sessions == roi_sessions,
            "Portfolio and ROI session counts do not match.",
        )

        require(
            portfolio_sessions <= economics_sessions,
            (
                "Portfolio contains more sessions than "
                "the intervention economics dataset."
            ),
        )

        print(
            f"Source sessions: {churn_sessions:,}"
        )

        print(
            f"Portfolio sessions: {portfolio_sessions:,}"
        )

        print(
            f"ROI sessions: {roi_sessions:,}"
        )

        print("\nCOMPLETE END-TO-END PIPELINE VALIDATION PASSED")

    finally:
        connection.close()


if __name__ == "__main__":
    main()