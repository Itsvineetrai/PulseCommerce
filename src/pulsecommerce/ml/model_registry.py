"""Model persistence utilities for PulseCommerce."""

from __future__ import annotations

from pathlib import Path

import joblib

from sklearn.pipeline import Pipeline


ARTIFACTS_DIRECTORY = Path("artifacts")

MODEL_PATH = (
    ARTIFACTS_DIRECTORY
    / "churn_model.joblib"
)


def save_model(
    model: Pipeline,
) -> Path:
    """Persist a trained churn model to disk."""

    ARTIFACTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        model,
        MODEL_PATH,
    )

    return MODEL_PATH


def load_model() -> Pipeline:
    """Load the persisted churn model."""

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            "Churn model artifact was not found. "
            "Run the final model training script first."
        )

    return joblib.load(
        MODEL_PATH
    )