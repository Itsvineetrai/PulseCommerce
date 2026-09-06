"""Inspect probability calibration for the PulseCommerce churn model."""

from __future__ import annotations

from pathlib import Path

import duckdb

from sklearn.model_selection import train_test_split

from pulsecommerce.ml.feature_config import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
)
from pulsecommerce.ml.model_comparison import (
    build_hist_gradient_boosting_model,
)
from pulsecommerce.ml.probability_diagnostics import (
    build_calibration_curve,
    build_calibration_table,
    build_probability_summary,
    calculate_brier_score,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)

TEST_SIZE = 0.20
RANDOM_STATE = 42


def load_feature_dataset():
    """Load the churn feature dataset."""

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


def main() -> None:
    """Inspect probability calibration on the held-out test set."""

    print(
        "PulseCommerce Probability Calibration Diagnostics"
    )

    print("-" * 60)

    dataset = load_feature_dataset()

    features = dataset[
        FEATURE_COLUMNS
    ]

    target = dataset[
        TARGET_COLUMN
    ]

    (
        x_train,
        x_test,
        y_train,
        y_test,
    ) = train_test_split(
        features,
        target,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=target,
    )

    print()
    print("1. DATA SPLIT")

    print(
        f"Training sessions: {len(x_train):,}"
    )

    print(
        f"Test sessions:     {len(x_test):,}"
    )

    model = (
        build_hist_gradient_boosting_model()
    )

    model.fit(
        x_train,
        y_train,
    )

    probabilities = model.predict_proba(
        x_test
    )[:, 1]

    print()
    print("2. BRIER SCORE")

    brier_score = (
        calculate_brier_score(
            actual=y_test,
            probabilities=probabilities,
        )
    )

    print(
        f"Brier score: {brier_score:.6f}"
    )

    print()
    print("3. PROBABILITY DISTRIBUTION")

    probability_summary = (
        build_probability_summary(
            probabilities
        )
        .round(4)
    )

    print(
        probability_summary.to_string()
    )

    print()
    print("4. CALIBRATION TABLE")

    calibration_table = (
        build_calibration_table(
            actual=y_test,
            probabilities=probabilities,
            n_bins=10,
        )
    )

    print(
        calibration_table.to_string(
            index=False,
            formatters={
                "average_predicted_probability_pct":
                    "{:.2f}".format,
                "actual_churn_rate_pct":
                    "{:.2f}".format,
                "calibration_gap_pct":
                    "{:+.2f}".format,
            },
        )
    )

    print()
    print("5. CALIBRATION CURVE POINTS")

    calibration_curve_points = (
        build_calibration_curve(
            actual=y_test,
            probabilities=probabilities,
            n_bins=10,
        )
    )

    print(
        calibration_curve_points.to_string(
            index=False,
            formatters={
                "average_predicted_probability_pct":
                    "{:.2f}".format,
                "actual_churn_rate_pct":
                    "{:.2f}".format,
            },
        )
    )

    print()
    print(
        "PROBABILITY DIAGNOSTICS COMPLETE"
    )


if __name__ == "__main__":
    main()