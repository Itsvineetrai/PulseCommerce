"""Tests for experiment population SQL logic."""

from __future__ import annotations

from pathlib import Path

import duckdb


def test_experiment_population_sql(
    tmp_path: Path,
) -> None:
    """Verify user-level experiment population creation."""

    database_path = (
        tmp_path / "experiment.duckdb"
    )

    sql_path = Path(
        "sql/analytics/experiment_population.sql"
    )

    connection = duckdb.connect(
        str(database_path),
    )

    try:
        connection.execute(
            """
            CREATE TABLE events (
                user_id VARCHAR,
                experiment_id VARCHAR,
                variant VARCHAR,
                event_name VARCHAR
            )
            """
        )

        connection.execute(
            """
            INSERT INTO events VALUES
                (
                    'user_1',
                    'checkout_redesign',
                    'control',
                    'homepage_view'
                ),
                (
                    'user_1',
                    'checkout_redesign',
                    'control',
                    'purchase_complete'
                ),
                (
                    'user_2',
                    'checkout_redesign',
                    'treatment',
                    'homepage_view'
                ),
                (
                    'user_3',
                    'checkout_redesign',
                    'treatment',
                    'homepage_view'
                ),
                (
                    'user_3',
                    'checkout_redesign',
                    'treatment',
                    'purchase_complete'
                ),
                (
                    'user_4',
                    'checkout_redesign',
                    'control',
                    'product_click'
                )
            """
        )

        sql = sql_path.read_text(
            encoding="utf-8",
        )

        connection.execute(sql)

        results = connection.execute(
            """
            SELECT
                user_id,
                variant,
                converted
            FROM analytics_experiment_population
            ORDER BY user_id
            """
        ).fetchall()

    finally:
        connection.close()

    assert results == [
        ("user_1", "control", True),
        ("user_2", "treatment", False),
        ("user_3", "treatment", True),
    ]