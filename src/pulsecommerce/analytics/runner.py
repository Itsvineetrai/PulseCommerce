"""SQL analytics model runner for PulseCommerce."""

from __future__ import annotations

from pathlib import Path

import duckdb


DEFAULT_DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)

DEFAULT_SQL_DIRECTORY = Path(
    "sql/analytics"
)

SQL_MODELS = (
    "session_funnel.sql",
    "funnel_metrics.sql",
    "velocity_metrics.sql",
)


def run_analytics_models(
    *,
    database_path: Path = DEFAULT_DATABASE_PATH,
    sql_directory: Path = DEFAULT_SQL_DIRECTORY,
) -> None:
    """Execute all analytics SQL models in dependency order."""

    if not database_path.exists():
        raise FileNotFoundError(
            f"Warehouse database not found: {database_path}"
        )

    if not sql_directory.exists():
        raise FileNotFoundError(
            f"SQL directory not found: {sql_directory}"
        )

    connection = duckdb.connect(
        database=str(database_path),
    )

    try:
        for model_name in SQL_MODELS:
            model_path = sql_directory / model_name

            if not model_path.exists():
                raise FileNotFoundError(
                    f"SQL model not found: {model_path}"
                )

            sql = model_path.read_text(
                encoding="utf-8",
            )

            connection.execute(sql)

    finally:
        connection.close()