"""Inspect correlations between numeric churn model features."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from pulsecommerce.ml.feature_config import (
    NUMERIC_FEATURES,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


CORRELATION_THRESHOLD = 0.80


def load_numeric_features() -> pd.DataFrame:
    """Load numeric ML features."""

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        columns = ", ".join(
            NUMERIC_FEATURES
        )

        query = f"""
            SELECT
                {columns}
            FROM analytics_churn_feature_dataset
        """

        return connection.execute(
            query
        ).fetchdf()

    finally:
        connection.close()


def main() -> None:
    """Inspect numeric feature correlations."""

    print(
        "PulseCommerce Feature "
        "Correlation Analysis"
    )
    print("-" * 60)

    dataset = (
        load_numeric_features()
    )

    correlation_matrix = (
        dataset.corr(
            method="pearson"
        )
    )

    print()
    print(
        "1. NUMERIC FEATURE "
        "CORRELATION MATRIX"
    )

    print(
        correlation_matrix.round(3).to_string()
    )

    high_correlations: list[
        dict[str, object]
    ] = []

    for index, feature_a in enumerate(
        correlation_matrix.columns
    ):
        for feature_b in (
            correlation_matrix.columns[
                index + 1:
            ]
        ):

            correlation = (
                correlation_matrix.loc[
                    feature_a,
                    feature_b,
                ]
            )

            if (
                abs(correlation)
                >= CORRELATION_THRESHOLD
            ):
                high_correlations.append(
                    {
                        "feature_a":
                            feature_a,
                        "feature_b":
                            feature_b,
                        "correlation":
                            correlation,
                        "absolute_correlation":
                            abs(correlation),
                    }
                )

    print()
    print(
        "2. HIGHLY CORRELATED "
        f"FEATURE PAIRS (|r| >= "
        f"{CORRELATION_THRESHOLD:.2f})"
    )

    if high_correlations:

        results = pd.DataFrame(
            high_correlations
        ).sort_values(
            by="absolute_correlation",
            ascending=False,
        )

        print(
            results[
                [
                    "feature_a",
                    "feature_b",
                    "correlation",
                ]
            ].to_string(
                index=False
            )
        )

    else:
        print(
            "No highly correlated "
            "feature pairs found."
        )

    print()
    print(
        "CORRELATION ANALYSIS COMPLETE"
    )


if __name__ == "__main__":
    main()