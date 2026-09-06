"""Feature dataset service for PulseCommerce churn modeling."""

from __future__ import annotations

from pathlib import Path

import duckdb


DEFAULT_DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)

DEFAULT_SQL_PATH = Path(
    "sql/analytics/churn_feature_dataset.sql"
)


def build_churn_feature_dataset(
    *,
    database_path: Path = DEFAULT_DATABASE_PATH,
    sql_path: Path = DEFAULT_SQL_PATH,
) -> None:
    """Build the leakage-safe churn feature dataset."""

    if not database_path.exists():
        raise FileNotFoundError(
            f"Warehouse database not found: {database_path}"
        )

    if not sql_path.exists():
        raise FileNotFoundError(
            f"Feature SQL not found: {sql_path}"
        )

    sql = sql_path.read_text(
        encoding="utf-8"
    )

    connection = duckdb.connect(
        str(database_path)
    )

    try:
        connection.execute(sql)

    finally:
        connection.close()