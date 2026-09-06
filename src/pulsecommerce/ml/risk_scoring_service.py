"""Churn risk scoring service for PulseCommerce."""

from __future__ import annotations

import pandas as pd

from pulsecommerce.ml.feature_config import FEATURE_COLUMNS
from pulsecommerce.ml.model_registry import load_model


LOW_RISK_THRESHOLD = 0.50
MEDIUM_RISK_THRESHOLD = 0.70
HIGH_RISK_THRESHOLD = 0.85


def assign_risk_band(
    churn_probability: float,
) -> str:
    """Assign a business-friendly risk band."""

    if churn_probability < LOW_RISK_THRESHOLD:
        return "low"

    if churn_probability < MEDIUM_RISK_THRESHOLD:
        return "medium"

    if churn_probability < HIGH_RISK_THRESHOLD:
        return "high"

    return "critical"


def score_churn_risk(
    feature_dataset: pd.DataFrame,
) -> pd.DataFrame:
    """Generate churn risk predictions for the feature dataset."""

    model = load_model()

    features = feature_dataset[
        FEATURE_COLUMNS
    ]

    probabilities = model.predict_proba(
        features
    )[:, 1]

    scored_dataset = feature_dataset[
        [
            "user_id",
            "session_id",
            "observation_timestamp",
            "has_cart",
            "reached_checkout",
            "purchased",
        ]
    ].copy()

    scored_dataset[
        "churn_probability"
    ] = probabilities

    scored_dataset[
        "churn_risk_score"
    ] = (
        scored_dataset[
            "churn_probability"
        ]
        * 100
    )

    scored_dataset[
        "risk_band"
    ] = scored_dataset[
        "churn_probability"
    ].apply(
        assign_risk_band
    )

    return scored_dataset