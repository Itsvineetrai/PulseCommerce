"""Model training utilities for PulseCommerce."""

from __future__ import annotations

from typing import Any

import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.preprocessing import StandardScaler

from pulsecommerce.ml.feature_config import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
)


def build_baseline_model() -> Pipeline:
    """Build the baseline churn prediction pipeline."""

    numeric_transformer = Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_transformer = Pipeline(
        steps=[
            (
                "encoder",
                OneHotEncoder(
                    handle_unknown="ignore",
                ),
            ),
        ]
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

    pipeline = Pipeline(
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

    return pipeline


def train_baseline_model(
    features: pd.DataFrame,
    target: pd.Series,
) -> Pipeline:
    """Train the baseline churn prediction model."""

    pipeline = build_baseline_model()

    pipeline.fit(
        features,
        target,
    )

    return pipeline


def predict_churn_probability(
    model: Pipeline,
    features: pd.DataFrame,
) -> pd.Series:
    """Predict probability of session abandonment."""

    probabilities = model.predict_proba(
        features
    )[:, 1]

    return pd.Series(
        probabilities,
        index=features.index,
        name="churn_probability",
    )


def get_model_coefficients(
    model: Pipeline,
) -> pd.DataFrame:
    """Extract Logistic Regression feature coefficients."""

    preprocessor = model.named_steps[
        "preprocessor"
    ]

    classifier = model.named_steps[
        "model"
    ]

    feature_names = (
        preprocessor.get_feature_names_out()
    )

    coefficients = classifier.coef_[0]

    results = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": coefficients,
            "absolute_coefficient": abs(
                coefficients
            ),
        }
    )

    return results.sort_values(
        by="absolute_coefficient",
        ascending=False,
    ).reset_index(
        drop=True
    )