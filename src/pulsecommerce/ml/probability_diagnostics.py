"""Probability diagnostics for PulseCommerce churn prediction."""

from __future__ import annotations

import numpy as np
import pandas as pd

from sklearn.calibration import calibration_curve
from sklearn.metrics import brier_score_loss


def calculate_brier_score(
    actual: pd.Series,
    probabilities: np.ndarray,
) -> float:
    """Calculate the Brier score for predicted probabilities."""

    return float(
        brier_score_loss(
            actual,
            probabilities,
        )
    )


def build_calibration_table(
    actual: pd.Series,
    probabilities: np.ndarray,
    n_bins: int = 10,
) -> pd.DataFrame:
    """Build a reliability table using probability bins."""

    frame = pd.DataFrame(
        {
            "actual_churn": actual.to_numpy(),
            "predicted_probability": probabilities,
        }
    )

    frame["probability_bin"] = pd.cut(
        frame["predicted_probability"],
        bins=np.linspace(0.0, 1.0, n_bins + 1),
        include_lowest=True,
    )

    calibration_table = (
        frame.groupby(
            "probability_bin",
            observed=False,
        )
        .agg(
            sessions=(
                "actual_churn",
                "size",
            ),
            average_predicted_probability=(
                "predicted_probability",
                "mean",
            ),
            actual_churn_rate=(
                "actual_churn",
                "mean",
            ),
        )
        .reset_index()
    )

    calibration_table[
        "average_predicted_probability_pct"
    ] = (
        calibration_table[
            "average_predicted_probability"
        ]
        * 100
    )

    calibration_table[
        "actual_churn_rate_pct"
    ] = (
        calibration_table[
            "actual_churn_rate"
        ]
        * 100
    )

    calibration_table[
        "calibration_gap_pct"
    ] = (
        calibration_table[
            "actual_churn_rate_pct"
        ]
        - calibration_table[
            "average_predicted_probability_pct"
        ]
    )

    return calibration_table[
        [
            "probability_bin",
            "sessions",
            "average_predicted_probability_pct",
            "actual_churn_rate_pct",
            "calibration_gap_pct",
        ]
    ]


def build_calibration_curve(
    actual: pd.Series,
    probabilities: np.ndarray,
    n_bins: int = 10,
) -> pd.DataFrame:
    """Build calibration curve values."""

    actual_rate, predicted_probability = calibration_curve(
        actual,
        probabilities,
        n_bins=n_bins,
        strategy="uniform",
    )

    return pd.DataFrame(
        {
            "average_predicted_probability_pct": (
                predicted_probability * 100
            ),
            "actual_churn_rate_pct": (
                actual_rate * 100
            ),
        }
    )


def build_probability_summary(
    probabilities: np.ndarray,
) -> pd.Series:
    """Return summary statistics for predicted probabilities."""

    return pd.Series(
        probabilities
    ).describe(
        percentiles=[
            0.05,
            0.10,
            0.25,
            0.50,
            0.75,
            0.90,
            0.95,
        ]
    )