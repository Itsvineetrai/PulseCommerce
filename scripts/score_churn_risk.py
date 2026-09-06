"""Generate churn risk scores for PulseCommerce sessions."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd
from pulsecommerce.ml.risk_scoring_service import (
    score_churn_risk,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


def load_feature_dataset() -> pd.DataFrame:
    """Load churn features from DuckDB."""

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        return connection.execute(
            """
            SELECT *
            FROM analytics_churn_feature_dataset
            """
        ).fetchdf()

    finally:
        connection.close()


def save_risk_scores(
    risk_scores: pd.DataFrame,
) -> None:
    """Persist churn risk scores to DuckDB."""

    connection = duckdb.connect(
        str(DATABASE_PATH)
    )

    try:
        connection.execute(
            """
            CREATE OR REPLACE TABLE
            analytics_churn_risk_scores AS
            SELECT *
            FROM risk_scores
            """
        )

    finally:
        connection.close()


def main() -> None:
    """Generate and store churn risk scores."""

    print(
        "PulseCommerce Churn Risk Scoring"
    )

    print("-" * 60)

    feature_dataset = (
        load_feature_dataset()
    )

    print()
    print(
        "1. LOADED FEATURE DATASET"
    )

    print(
        f"Sessions: "
        f"{len(feature_dataset):,}"
    )

    risk_scores = score_churn_risk(
        feature_dataset
    )

    print()
    print(
        "2. GENERATED RISK SCORES"
    )

    print(
        risk_scores[
            "churn_risk_score"
        ]
        .describe()
        .round(2)
        .to_string()
    )

    save_risk_scores(
        risk_scores
    )

    print()
    print(
        "3. RISK BAND DISTRIBUTION"
    )

    distribution = (
        risk_scores[
            "risk_band"
        ]
        .value_counts()
        .rename_axis(
            "risk_band"
        )
        .reset_index(
            name="sessions"
        )
    )

    print(
        distribution.to_string(
            index=False
        )
    )

    print()
    print(
        "RISK SCORING COMPLETE"
    )


if __name__ == "__main__":
    main()