"""Train and evaluate the PulseCommerce baseline churn model."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    classification_report,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import (
    train_test_split,
)

from pulsecommerce.ml.feature_config import (
    FEATURE_COLUMNS,
    TARGET_COLUMN,
)
from pulsecommerce.ml.model_service import (
    get_model_coefficients,
    predict_churn_probability,
    train_baseline_model,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


TEST_SIZE = 0.20
RANDOM_STATE = 42


def load_training_data() -> pd.DataFrame:
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
    """Train and evaluate the baseline model."""

    print("PulseCommerce Baseline Churn Model")
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
        f"Training sessions: "
        f"{len(x_train):,}"
    )

    print(
        f"Test sessions:     "
        f"{len(x_test):,}"
    )

    print()
    print("2. TRAINING MODEL")

    model = train_baseline_model(
        x_train,
        y_train,
    )

    print(
        "Baseline Logistic Regression "
        "trained successfully."
    )

    predictions = model.predict(
        x_test
    )

    probabilities = (
        predict_churn_probability(
            model,
            x_test,
        )
    )

    print()
    print("3. MODEL PERFORMANCE")

    accuracy = accuracy_score(
        y_test,
        predictions,
    )

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0,
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0,
    )

    roc_auc = roc_auc_score(
        y_test,
        probabilities,
    )

    print(
        f"Accuracy:  "
        f"{accuracy:.4f}"
    )

    print(
        f"Precision: "
        f"{precision:.4f}"
    )

    print(
        f"Recall:    "
        f"{recall:.4f}"
    )

    print(
        f"ROC-AUC:   "
        f"{roc_auc:.4f}"
    )

    print()
    print("4. CLASSIFICATION REPORT")

    print(
        classification_report(
            y_test,
            predictions,
            digits=4,
        )
    )

    print()
    print("5. TOP FEATURE SIGNALS")

    coefficients = (
        get_model_coefficients(
            model
        )
    )

    print(
        coefficients.head(10).to_string(
            index=False
        )
    )

    print()
    print("BASELINE MODEL TRAINING COMPLETE")


if __name__ == "__main__":
    main()