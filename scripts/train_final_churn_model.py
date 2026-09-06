"""Train and persist the final PulseCommerce churn model."""

from __future__ import annotations

from pathlib import Path

import duckdb

from pulsecommerce.ml.feature_config import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
)
from pulsecommerce.ml.model_comparison import (
    build_hist_gradient_boosting_model,
)
from pulsecommerce.ml.model_registry import (
    save_model,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


def load_training_data():
    """Load the validated churn feature dataset."""

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
    """Train the final churn model."""

    print("PulseCommerce Final Churn Model Training")
    print("-" * 60)

    dataset = load_training_data()

    features = dataset[
        FEATURE_COLUMNS
    ]

    target = dataset[
        TARGET_COLUMN
    ]

    print()
    print("1. TRAINING DATA")

    print(
        f"Total sessions: "
        f"{len(features):,}"
    )

    print(
        f"Total features: "
        f"{len(FEATURE_COLUMNS)}"
    )

    print()
    print("2. FINAL MODEL")

    model = (
        build_hist_gradient_boosting_model()
    )

    print(
        "Model: "
        "HistGradientBoostingClassifier"
    )

    print()
    print("3. TRAINING")

    model.fit(
        features,
        target,
    )

    print(
        "Final model trained successfully."
    )

    print()
    print("4. MODEL PERSISTENCE")

    model_path = save_model(
        model
    )

    print(
        f"Model saved to: "
        f"{model_path}"
    )

    print()
    print(
        "FINAL CHURN MODEL TRAINING COMPLETE"
    )


if __name__ == "__main__":
    main()