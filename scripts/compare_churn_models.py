"""Compare candidate churn models for PulseCommerce."""

from __future__ import annotations

from pathlib import Path

import duckdb

from sklearn.model_selection import train_test_split

from pulsecommerce.ml.feature_config import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
)
from pulsecommerce.ml.model_comparison import (
    compare_models,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)

TEST_SIZE = 0.20
RANDOM_STATE = 42


def load_training_data():
    """Load the churn feature dataset from DuckDB."""

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
    """Compare churn prediction models."""

    print("PulseCommerce Churn Model Comparison")
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

    print()
    print("1. DATA SPLIT")

    print(
        f"Training sessions: {len(x_train):,}"
    )

    print(
        f"Test sessions:     {len(x_test):,}"
    )

    print()
    print("2. MODEL COMPARISON")

    results = compare_models(
        x_train=x_train,
        y_train=y_train,
        x_test=x_test,
        y_test=y_test,
    )

    print(
        results.to_string(
            index=False,
            formatters={
                "accuracy": "{:.4f}".format,
                "precision": "{:.4f}".format,
                "recall": "{:.4f}".format,
                "f1_score": "{:.4f}".format,
                "roc_auc": "{:.4f}".format,
            },
        )
    )

    best_model = results.iloc[0]

    print()
    print("3. BEST MODEL BY ROC-AUC")

    print(
        f"Selected model: "
        f"{best_model['model']}"
    )

    print(
        f"ROC-AUC: "
        f"{best_model['roc_auc']:.4f}"
    )

    print()
    print(
        "MODEL COMPARISON COMPLETE"
    )


if __name__ == "__main__":
    main()