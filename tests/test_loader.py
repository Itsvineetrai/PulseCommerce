"""Tests for PulseCommerce warehouse loading."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

from pulsecommerce.warehouse.loader import (
    load_events_to_warehouse,
)


def create_test_parquet(path: Path) -> None:
    """Create a valid Parquet event file."""

    table = pa.table(
        {
            "event_id": [
                "event-001",
                "event-002",
            ],
            "user_id": [
                "user-001",
                "user-002",
            ],
            "session_id": [
                "session-001",
                "session-002",
            ],
            "event_timestamp": [
                "2026-01-01 10:00:00",
                "2026-01-01 11:00:00",
            ],
            "event_name": [
                "homepage_view",
                "product_view",
            ],
            "experiment_id": [
                "EXP-001",
                "EXP-001",
            ],
            "variant": [
                "control",
                "treatment",
            ],
        }
    )

    pq.write_table(
        table,
        path,
    )


def test_load_events_to_warehouse(
    tmp_path: Path,
) -> None:
    landing_directory = tmp_path / "landing"
    landing_directory.mkdir()

    parquet_path = (
        landing_directory / "events.parquet"
    )

    database_path = (
        tmp_path / "pulsecommerce.duckdb"
    )

    create_test_parquet(parquet_path)

    report = load_events_to_warehouse(
        database_path=database_path,
        landing_path=str(
            landing_directory / "*.parquet"
        ),
    )

    assert report.is_valid
    assert report.total_rows == 2

    connection = duckdb.connect(
        str(database_path),
        read_only=True,
    )

    try:
        row_count = connection.execute(
            """
            SELECT COUNT(*)
            FROM events
            """
        ).fetchone()[0]

        assert row_count == 2

    finally:
        connection.close()