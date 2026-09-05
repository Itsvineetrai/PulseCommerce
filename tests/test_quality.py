"""Tests for PulseCommerce data quality validation."""

from __future__ import annotations

from datetime import datetime

import duckdb

from pulsecommerce.warehouse.quality import validate_events


def create_connection() -> duckdb.DuckDBPyConnection:
    """Create an in-memory DuckDB connection."""

    return duckdb.connect(":memory:")


def create_valid_events_table(
    connection: duckdb.DuckDBPyConnection,
) -> None:
    """Create a valid event relation for testing."""

    connection.execute(
        """
        CREATE TABLE events AS
        SELECT
            'event-001' AS event_id,
            'user-001' AS user_id,
            'session-001' AS session_id,
            CAST(
                '2026-01-01 10:00:00'
                AS TIMESTAMP
            ) AS event_timestamp,
            'homepage_view' AS event_name,
            'EXP-001' AS experiment_id,
            'control' AS variant
        """
    )


def test_valid_events_pass_quality_checks() -> None:
    connection = create_connection()

    try:
        create_valid_events_table(connection)

        report = validate_events(
            connection,
            "events",
        )

        assert report.is_valid
        assert report.total_rows == 1

    finally:
        connection.close()


def test_duplicate_event_ids_fail_quality_check() -> None:
    connection = create_connection()

    try:
        connection.execute(
            """
            CREATE TABLE events AS
            SELECT * FROM (
                VALUES
                    (
                        'event-001',
                        'user-001',
                        'session-001',
                        TIMESTAMP '2026-01-01 10:00:00',
                        'homepage_view',
                        'EXP-001',
                        'control'
                    ),
                    (
                        'event-001',
                        'user-002',
                        'session-002',
                        TIMESTAMP '2026-01-01 11:00:00',
                        'homepage_view',
                        'EXP-001',
                        'treatment'
                    )
            ) AS t(
                event_id,
                user_id,
                session_id,
                event_timestamp,
                event_name,
                experiment_id,
                variant
            )
            """
        )

        report = validate_events(
            connection,
            "events",
        )

        assert not report.is_valid
        assert report.duplicate_event_ids == 1

    finally:
        connection.close()


def test_invalid_event_name_fails_quality_check() -> None:
    connection = create_connection()

    try:
        connection.execute(
            """
            CREATE TABLE events AS
            SELECT
                'event-001' AS event_id,
                'user-001' AS user_id,
                'session-001' AS session_id,
                TIMESTAMP '2026-01-01 10:00:00'
                    AS event_timestamp,
                'invalid_event' AS event_name,
                'EXP-001' AS experiment_id,
                'control' AS variant
            """
        )

        report = validate_events(
            connection,
            "events",
        )

        assert not report.is_valid
        assert report.invalid_event_names == 1

    finally:
        connection.close()


def test_invalid_variant_fails_quality_check() -> None:
    connection = create_connection()

    try:
        connection.execute(
            """
            CREATE TABLE events AS
            SELECT
                'event-001' AS event_id,
                'user-001' AS user_id,
                'session-001' AS session_id,
                TIMESTAMP '2026-01-01 10:00:00'
                    AS event_timestamp,
                'homepage_view' AS event_name,
                'EXP-001' AS experiment_id,
                'invalid_variant' AS variant
            """
        )

        report = validate_events(
            connection,
            "events",
        )

        assert not report.is_valid
        assert report.invalid_variants == 1

    finally:
        connection.close()