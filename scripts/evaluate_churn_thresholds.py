"""Evaluate PulseCommerce churn risk thresholds."""

from __future__ import annotations

from pathlib import Path

import duckdb

from sklearn.model_selection import train_test_split

from pulsecommerce.ml.evaluation_service import (
    calculate_high_risk_summary,
    evaluate_thresholds,
)
from pulsecommerce.ml.feature_config import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
)
from pulsecommerce.ml.model_service import (
    predict_churn_probability,
    train_baseline_model,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


TEST_SIZE = 0.20
RANDOM_STATE = 42


THRESHOLDS = [
    0.50,
    0.60,
    0.70,
    0.75,
    0.80,
    0.90,
]


def load_training_data():
    """Load churn features from the warehouse."""

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
    """Train the baseline model and evaluate thresholds."""

    print("PulseCommerce Churn Threshold Analysis")
    print("-" * 60)

    dataset = load_training_data()

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

    model = train_baseline_model(
        x_train,
        y_train,
    )

    probabilities = (
        predict_churn_probability(
            model,
            x_test,
        )
    )

    print()
    print("1. THRESHOLD PERFORMANCE")

    results = evaluate_thresholds(
        probabilities=probabilities,
        target=y_test,
        thresholds=THRESHOLDS,
    )

    print(
        results.to_string(
            index=False,
            formatters={
                "threshold": "{:.2f}".format,
                "flagged_percentage":
                    "{:.2f}".format,
                "accuracy": "{:.4f}".format,
                "precision": "{:.4f}".format,
                "recall": "{:.4f}".format,
            },
        )
    )

    intervention_threshold = 0.75

    print()
    print(
        "2. HIGH-RISK INTERVENTION SUMMARY "
        f"(THRESHOLD >= {intervention_threshold:.2f})"
    )

    summary = calculate_high_risk_summary(
        probabilities=probabilities,
        target=y_test,
        threshold=intervention_threshold,
    )

    for key, value in summary.items():

        if isinstance(
            value,
            float,
        ):
            print(
                f"{key}: {value:.4f}"
            )
        else:
            print(
                f"{key}: {value}"
            )

    print()
    print(
        "THRESHOLD ANALYSIS COMPLETE"
    )


if __name__ == "__main__":
    main()