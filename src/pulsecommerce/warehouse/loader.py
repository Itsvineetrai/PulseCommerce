"""DuckDB warehouse loading for PulseCommerce."""

from __future__ import annotations

from pathlib import Path

import duckdb

from pulsecommerce.warehouse.quality import (
    QualityReport,
    validate_events,
)


DEFAULT_DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)

DEFAULT_LANDING_PATH = (
    "data/landing/events/*.parquet"
)


def load_events_to_warehouse(
    *,
    database_path: Path = DEFAULT_DATABASE_PATH,
    landing_path: str = DEFAULT_LANDING_PATH,
) -> QualityReport:
    """Load landing events into the canonical DuckDB warehouse.

    Data quality validation runs before the canonical table is replaced.
    The existing warehouse remains unchanged if validation fails.
    """

    database_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    connection = duckdb.connect(
        database=str(database_path),
    )

    try:
        connection.execute(
            f"""
            CREATE OR REPLACE TEMP VIEW staging_events AS
            SELECT *
            FROM read_parquet('{landing_path}')
            """
        )

        quality_report = validate_events(
            connection,
            "staging_events",
        )

        if not quality_report.is_valid:
            raise ValueError(
                "Data quality validation failed: "
                f"{quality_report}"
            )

        connection.execute(
            """
            BEGIN TRANSACTION
            """
        )

        try:
            connection.execute(
                """
                CREATE OR REPLACE TABLE events AS
                SELECT *
                FROM staging_events
                """
            )

            connection.execute(
                """
                COMMIT
                """
            )

        except Exception:
            connection.execute(
                """
                ROLLBACK
                """
            )
            raise

        return quality_report

    finally:
        connection.close()