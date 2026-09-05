"""Tests for PulseCommerce analytics SQL models."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pytest

from pulsecommerce.analytics.runner import (
    run_analytics_models,
)


@pytest.fixture
def analytics_database(
    tmp_path: Path,
) -> tuple[Path, Path]:
    """Create an isolated warehouse and SQL model directory."""

    database_path = tmp_path / "analytics.duckdb"

    sql_directory = tmp_path / "sql"
    sql_directory.mkdir()

    connection = duckdb.connect(
        str(database_path),
    )

    try:
        connection.execute(
            """
            CREATE TABLE events (
                event_id VARCHAR,
                user_id VARCHAR,
                session_id VARCHAR,
                event_timestamp TIMESTAMP,
                event_name VARCHAR
            )
            """
        )

        connection.execute(
            """
            INSERT INTO events VALUES
                (
                    'e1',
                    'u1',
                    's1',
                    TIMESTAMP '2026-01-01 10:00:00',
                    'homepage_view'
                ),
                (
                    'e2',
                    'u1',
                    's1',
                    TIMESTAMP '2026-01-01 10:01:00',
                    'product_click'
                ),
                (
                    'e3',
                    'u1',
                    's1',
                    TIMESTAMP '2026-01-01 10:02:00',
                    'add_to_cart'
                ),
                (
                    'e4',
                    'u1',
                    's1',
                    TIMESTAMP '2026-01-01 10:05:00',
                    'purchase_complete'
                ),
                (
                    'e5',
                    'u2',
                    's2',
                    TIMESTAMP '2026-01-01 11:00:00',
                    'homepage_view'
                ),
                (
                    'e6',
                    'u2',
                    's2',
                    TIMESTAMP '2026-01-01 11:02:00',
                    'product_click'
                )
            """
        )

    finally:
        connection.close()

    return database_path, sql_directory


def write_sql_models(
    sql_directory: Path,
) -> None:
    """Create minimal SQL models for integration testing."""

    models = {
        "session_funnel.sql": """
            CREATE OR REPLACE TABLE analytics_session_funnel AS
            SELECT
                session_id,
                user_id,
                MIN(
                    CASE
                        WHEN event_name = 'homepage_view'
                        THEN event_timestamp
                    END
                ) AS homepage_view_at,
                MIN(
                    CASE
                        WHEN event_name = 'product_click'
                        THEN event_timestamp
                    END
                ) AS product_click_at,
                MIN(
                    CASE
                        WHEN event_name = 'add_to_cart'
                        THEN event_timestamp
                    END
                ) AS add_to_cart_at,
                MIN(
                    CASE
                        WHEN event_name = 'purchase_complete'
                        THEN event_timestamp
                    END
                ) AS purchase_complete_at
            FROM events
            GROUP BY
                session_id,
                user_id
        """,
        "funnel_metrics.sql": """
            CREATE OR REPLACE TABLE analytics_funnel_metrics AS
            SELECT
                'homepage_view' AS funnel_step,
                COUNT(*) AS sessions
            FROM analytics_session_funnel
        """,
        "velocity_metrics.sql": """
            CREATE OR REPLACE TABLE analytics_velocity_metrics AS
            SELECT
                session_id,
                user_id,
                COUNT(*) AS total_events
            FROM events
            GROUP BY
                session_id,
                user_id
        """,
    }

    for file_name, sql in models.items():
        model_path = sql_directory / file_name

        model_path.write_text(
            sql,
            encoding="utf-8",
        )


def test_run_analytics_models(
    analytics_database: tuple[Path, Path],
) -> None:
    database_path, sql_directory = analytics_database

    write_sql_models(sql_directory)

    run_analytics_models(
        database_path=database_path,
        sql_directory=sql_directory,
    )

    connection = duckdb.connect(
        str(database_path),
        read_only=True,
    )

    try:
        funnel_table_exists = connection.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name =
                'analytics_session_funnel'
            """
        ).fetchone()[0]

        metrics_table_exists = connection.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name =
                'analytics_funnel_metrics'
            """
        ).fetchone()[0]

        velocity_table_exists = connection.execute(
            """
            SELECT COUNT(*)
            FROM information_schema.tables
            WHERE table_name =
                'analytics_velocity_metrics'
            """
        ).fetchone()[0]

        assert funnel_table_exists == 1
        assert metrics_table_exists == 1
        assert velocity_table_exists == 1

        session_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM analytics_session_funnel
            """
        ).fetchone()[0]

        assert session_count == 2

    finally:
        connection.close()