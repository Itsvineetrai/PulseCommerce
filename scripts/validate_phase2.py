"""Phase 2 validation for the PulseCommerce DuckDB warehouse."""

from __future__ import annotations

from pathlib import Path

import duckdb


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)

LANDING_PATH = "data/landing/events/*.parquet"


def print_section(title: str) -> None:
    """Print a formatted validation section."""

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main() -> None:
    """Validate the PulseCommerce DuckDB warehouse."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Warehouse database not found: {DATABASE_PATH}"
        )

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        # -----------------------------------------------------------
        # 1. Warehouse objects
        # -----------------------------------------------------------

        print_section("1. WAREHOUSE OBJECTS")

        tables = connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
            ORDER BY table_name
            """
        ).fetchdf()

        print(tables.to_string(index=False))

        if "events" not in tables["table_name"].tolist():
            raise ValueError(
                "Canonical events table does not exist."
            )

        # -----------------------------------------------------------
        # 2. Schema inspection
        # -----------------------------------------------------------

        print_section("2. EVENTS TABLE SCHEMA")

        schema = connection.execute(
            """
            DESCRIBE events
            """
        ).fetchdf()

        print(schema.to_string(index=False))

        # -----------------------------------------------------------
        # 3. Warehouse overview
        # -----------------------------------------------------------

        print_section("3. WAREHOUSE OVERVIEW")

        overview = connection.execute(
            """
            SELECT
                COUNT(*) AS total_events,
                COUNT(DISTINCT user_id) AS total_users,
                COUNT(DISTINCT session_id) AS total_sessions,
                MIN(event_timestamp) AS first_event,
                MAX(event_timestamp) AS last_event
            FROM events
            """
        ).fetchdf()

        print(overview.to_string(index=False))

        # -----------------------------------------------------------
        # 4. Landing vs warehouse reconciliation
        # -----------------------------------------------------------

        print_section(
            "4. LANDING VS WAREHOUSE RECONCILIATION"
        )

        reconciliation = connection.execute(
            f"""
            WITH landing AS (
                SELECT COUNT(*) AS row_count
                FROM read_parquet('{LANDING_PATH}')
            ),
            warehouse AS (
                SELECT COUNT(*) AS row_count
                FROM events
            )
            SELECT
                landing.row_count AS landing_rows,
                warehouse.row_count AS warehouse_rows,
                landing.row_count - warehouse.row_count
                    AS row_difference
            FROM landing
            CROSS JOIN warehouse
            """
        ).fetchdf()

        print(reconciliation.to_string(index=False))

        row_difference = reconciliation[
            "row_difference"
        ].iloc[0]

        if row_difference != 0:
            raise ValueError(
                "Landing and warehouse row counts do not match."
            )

        # -----------------------------------------------------------
        # 5. Experiment integrity
        # -----------------------------------------------------------

        print_section("5. EXPERIMENT INTEGRITY")

        experiment_integrity = connection.execute(
            """
            SELECT
                user_id,
                COUNT(DISTINCT experiment_id)
                    AS experiment_count,
                COUNT(DISTINCT variant)
                    AS variant_count
            FROM events
            GROUP BY user_id
            HAVING
                COUNT(DISTINCT experiment_id) != 1
                OR COUNT(DISTINCT variant) != 1
            """
        ).fetchdf()

        inconsistent_users = len(
            experiment_integrity
        )

        print(
            "Users with inconsistent experiment "
            f"assignment: {inconsistent_users}"
        )

        if inconsistent_users > 0:
            print(
                experiment_integrity.to_string(
                    index=False
                )
            )
            raise ValueError(
                "Experiment assignment is not stable."
            )

        # -----------------------------------------------------------
        # 6. Session boundary integrity
        # -----------------------------------------------------------

        print_section("6. SESSION BOUNDARY INTEGRITY")

        session_integrity = connection.execute(
            """
            WITH session_events AS (
                SELECT
                    session_id,
                    COUNT(
                        CASE
                            WHEN event_name = 'session_start'
                            THEN 1
                        END
                    ) AS session_starts,
                    COUNT(
                        CASE
                            WHEN event_name = 'session_end'
                            THEN 1
                        END
                    ) AS session_ends
                FROM events
                GROUP BY session_id
            )
            SELECT
                COUNT(*) FILTER (
                    WHERE session_starts != 1
                ) AS invalid_session_starts,
                COUNT(*) FILTER (
                    WHERE session_ends != 1
                ) AS invalid_session_ends
            FROM session_events
            """
        ).fetchdf()

        print(session_integrity.to_string(index=False))

        invalid_starts = session_integrity[
            "invalid_session_starts"
        ].iloc[0]

        invalid_ends = session_integrity[
            "invalid_session_ends"
        ].iloc[0]

        if invalid_starts != 0 or invalid_ends != 0:
            raise ValueError(
                "Session boundary integrity check failed."
            )

        # -----------------------------------------------------------
        # 7. Canonical event coverage
        # -----------------------------------------------------------

        print_section("7. EVENT COVERAGE")

        event_coverage = connection.execute(
            """
            SELECT
                event_name,
                COUNT(*) AS event_count
            FROM events
            GROUP BY event_name
            ORDER BY event_name
            """
        ).fetchdf()

        print(event_coverage.to_string(index=False))

        # -----------------------------------------------------------
        # Final status
        # -----------------------------------------------------------

        print()
        print("=" * 70)
        print("PHASE 2 VALIDATION PASSED")
        print("=" * 70)

    finally:
        connection.close()


if __name__ == "__main__":
    main()