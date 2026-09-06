"""Evaluation utilities for PulseCommerce churn models."""

from __future__ import annotations

from typing import Iterable

import pandas as pd

from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
)


def evaluate_thresholds(
    probabilities: pd.Series,
    target: pd.Series,
    thresholds: Iterable[float],
) -> pd.DataFrame:
    """Evaluate model performance across probability thresholds."""

    results: list[dict[str, float | int]] = []

    for threshold in thresholds:
        predictions = (
            probabilities >= threshold
        ).astype(int)

        flagged_sessions = int(
            predictions.sum()
        )

        total_sessions = len(
            predictions
        )

        results.append(
            {
                "threshold": threshold,
                "flagged_sessions": flagged_sessions,
                "flagged_percentage": (
                    100.0
                    * flagged_sessions
                    / total_sessions
                ),
                "accuracy": accuracy_score(
                    target,
                    predictions,
                ),
                "precision": precision_score(
                    target,
                    predictions,
                    zero_division=0,
                ),
                "recall": recall_score(
                    target,
                    predictions,
                    zero_division=0,
                ),
            }
        )

    return pd.DataFrame(results)


def calculate_high_risk_summary(
    probabilities: pd.Series,
    target: pd.Series,
    threshold: float,
) -> dict[str, float | int]:
    """Summarize sessions above an intervention threshold."""

    predictions = (
        probabilities >= threshold
    ).astype(int)

    flagged_sessions = int(
        predictions.sum()
    )

    true_abandonments = int(
        (
            (predictions == 1)
            & (target == 1)
        ).sum()
    )

    false_positives = int(
        (
            (predictions == 1)
            & (target == 0)
        ).sum()
    )

    total_sessions = len(
        predictions
    )

    return {
        "threshold": threshold,
        "flagged_sessions": flagged_sessions,
        "flagged_percentage": (
            100.0
            * flagged_sessions
            / total_sessions
        ),
        "true_abandonments": true_abandonments,
        "false_positives": false_positives,
        "precision": precision_score(
            target,
            predictions,
            zero_division=0,
        ),
        "recall": recall_score(
            target,
            predictions,
            zero_division=0,
        ),
    }