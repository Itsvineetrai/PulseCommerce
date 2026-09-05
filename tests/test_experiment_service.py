"""Tests for PulseCommerce experimentation statistics."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from pulsecommerce.experiments.service import (
    analyze_conversion_experiment,
)


def create_experiment_database(
    database_path: Path,
) -> None:
    """Create a temporary experiment dataset."""

    connection = duckdb.connect(
        str(database_path),
    )

    try:
        connection.execute(
            """
            CREATE TABLE
            analytics_experiment_population (
                user_id VARCHAR,
                variant VARCHAR,
                converted BOOLEAN
            )
            """
        )

        rows = []

        for index in range(100):
            rows.append(
                (
                    f"control_{index}",
                    "control",
                    index < 10,
                )
            )

        for index in range(100):
            rows.append(
                (
                    f"treatment_{index}",
                    "treatment",
                    index < 30,
                )
            )

        connection.executemany(
            """
            INSERT INTO
            analytics_experiment_population
            VALUES (?, ?, ?)
            """,
            rows,
        )

    finally:
        connection.close()


def test_analyze_conversion_experiment(
    tmp_path: Path,
) -> None:
    """Verify experiment statistics and decision."""

    database_path = (
        tmp_path / "experiment.duckdb"
    )

    create_experiment_database(
        database_path
    )

    result = analyze_conversion_experiment(
        database_path=database_path
    )

    assert result.control_users == 100
    assert result.treatment_users == 100

    assert result.control_conversions == 10
    assert result.treatment_conversions == 30

    assert result.control_conversion_rate == 0.10
    assert result.treatment_conversion_rate == 0.30

    assert result.absolute_lift == pytest.approx(
        0.20
    )

    assert result.relative_lift == pytest.approx(
        2.0
    )

    assert result.statistically_significant
    assert result.confidence_interval_lower > 0
    assert result.confidence_interval_upper > 0

    assert (
        "Recommend rollout."
        in result.recommendation
    )


def test_invalid_significance_level(
    tmp_path: Path,
) -> None:
    """Reject invalid significance levels."""

    database_path = (
        tmp_path / "experiment.duckdb"
    )

    create_experiment_database(
        database_path
    )

    with pytest.raises(ValueError):
        analyze_conversion_experiment(
            database_path=database_path,
            significance_level=1.0,
        )