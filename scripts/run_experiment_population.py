"""Build the PulseCommerce experiment analysis population."""

from __future__ import annotations

from pathlib import Path

import duckdb


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)

SQL_PATH = Path(
    "sql/analytics/experiment_population.sql"
)


def main() -> None:
    """Execute the experiment population SQL model."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Warehouse database not found: {DATABASE_PATH}"
        )

    if not SQL_PATH.exists():
        raise FileNotFoundError(
            f"SQL model not found: {SQL_PATH}"
        )

    print("PulseCommerce Experiment Population")
    print("-" * 50)

    sql = SQL_PATH.read_text(
        encoding="utf-8",
    )

    connection = duckdb.connect(
        str(DATABASE_PATH),
    )

    try:
        connection.execute(sql)

        summary = connection.execute(
            """
            SELECT
                variant,
                COUNT(*) AS users,
                SUM(converted::INTEGER) AS conversions,
                ROUND(
                    100.0
                    * SUM(converted::INTEGER)
                    / COUNT(*),
                    2
                ) AS conversion_rate_pct
            FROM analytics_experiment_population
            GROUP BY variant
            ORDER BY variant
            """
        ).fetchdf()

        print(summary.to_string(index=False))

    finally:
        connection.close()

    print()
    print(
        "Experiment population created successfully."
    )


if __name__ == "__main__":
    main()