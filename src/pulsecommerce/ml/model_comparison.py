"""Model comparison utilities for PulseCommerce churn prediction."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from pulsecommerce.ml.feature_config import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)


@dataclass
class ModelEvaluation:
    """Container for churn model evaluation results."""

    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    roc_auc: float


def build_logistic_regression_model() -> Pipeline:
    """Build the Logistic Regression baseline pipeline."""

    numeric_transformer = Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_transformer = OneHotEncoder(
        handle_unknown="ignore",
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_transformer,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_transformer,
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    model = LogisticRegression(
        max_iter=1000,
        class_weight="balanced",
        random_state=42,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                model,
            ),
        ]
    )


def build_hist_gradient_boosting_model() -> Pipeline:
    """Build the HistGradientBoosting churn model pipeline."""

    numeric_transformer = Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_transformer = OneHotEncoder(
        handle_unknown="ignore",
        sparse_output=False,
    )

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_transformer,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_transformer,
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )

    model = HistGradientBoostingClassifier(
        learning_rate=0.05,
        max_iter=200,
        max_leaf_nodes=31,
        random_state=42,
    )

    return Pipeline(
        steps=[
            (
                "preprocessor",
                preprocessor,
            ),
            (
                "model",
                model,
            ),
        ]
    )


def evaluate_model(
    model_name: str,
    model: Pipeline,
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> ModelEvaluation:
    """Train and evaluate one churn model."""

    model.fit(
        x_train,
        y_train,
    )

    predictions = model.predict(
        x_test
    )

    probabilities = model.predict_proba(
        x_test
    )[:, 1]

    return ModelEvaluation(
        model_name=model_name,
        accuracy=accuracy_score(
            y_test,
            predictions,
        ),
        precision=precision_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        recall=recall_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        f1_score=f1_score(
            y_test,
            predictions,
            zero_division=0,
        ),
        roc_auc=roc_auc_score(
            y_test,
            probabilities,
        ),
    )


def compare_models(
    x_train: pd.DataFrame,
    y_train: pd.Series,
    x_test: pd.DataFrame,
    y_test: pd.Series,
) -> pd.DataFrame:
    """Train and compare all candidate churn models."""

    candidates = [
        (
            "Logistic Regression",
            build_logistic_regression_model(),
        ),
        (
            "HistGradientBoosting",
            build_hist_gradient_boosting_model(),
        ),
    ]

    results: list[dict[str, object]] = []

    for model_name, model in candidates:
        evaluation = evaluate_model(
            model_name=model_name,
            model=model,
            x_train=x_train,
            y_train=y_train,
            x_test=x_test,
            y_test=y_test,
        )

        results.append(
            {
                "model": evaluation.model_name,
                "accuracy": evaluation.accuracy,
                "precision": evaluation.precision,
                "recall": evaluation.recall,
                "f1_score": evaluation.f1_score,
                "roc_auc": evaluation.roc_auc,
            }
        )

    return pd.DataFrame(
        results
    ).sort_values(
        by="roc_auc",
        ascending=False,
    ).reset_index(
        drop=True
    )