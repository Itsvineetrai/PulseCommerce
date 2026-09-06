"""Tests for churn feature dataset integrity."""

from __future__ import annotations

import duckdb


def test_churn_feature_dataset_has_valid_labels(
    tmp_path,
) -> None:
    """Verify churn labels contain only binary values."""

    database_path = (
        tmp_path / "features.duckdb"
    )

    connection = duckdb.connect(
        str(database_path)
    )

    try:
        connection.execute(
            """
            CREATE TABLE features (
                churned INTEGER
            )
            """
        )

        connection.execute(
            """
            INSERT INTO features
            VALUES
                (0),
                (1),
                (0),
                (1)
            """
        )

        invalid_labels = connection.execute(
            """
            SELECT COUNT(*)
            FROM features
            WHERE churned NOT IN (0, 1)
               OR churned IS NULL
            """
        ).fetchone()[0]

    finally:
        connection.close()

    assert invalid_labels == 0


def test_churn_rate_is_calculated_correctly(
    tmp_path,
) -> None:
    """Verify churn-rate calculation."""

    database_path = (
        tmp_path / "features.duckdb"
    )

    connection = duckdb.connect(
        str(database_path)
    )

    try:
        connection.execute(
            """
            CREATE TABLE features (
                churned INTEGER
            )
            """
        )

        connection.execute(
            """
            INSERT INTO features
            VALUES
                (1),
                (1),
                (1),
                (0)
            """
        )

        churn_rate = connection.execute(
            """
            SELECT AVG(churned)
            FROM features
            """
        ).fetchone()[0]

    finally:
        connection.close()

    assert churn_rate == 0.75