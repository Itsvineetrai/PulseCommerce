"""Tests for the churn feature dataset service."""

from __future__ import annotations

from pathlib import Path

import pytest

from pulsecommerce.ml.feature_service import (
    build_churn_feature_dataset,
)


def test_missing_database_raises_error(
    tmp_path: Path,
) -> None:
    """Reject a missing warehouse database."""

    missing_database = (
        tmp_path / "missing.duckdb"
    )

    with pytest.raises(FileNotFoundError):
        build_churn_feature_dataset(
            database_path=missing_database
        )


def test_missing_sql_raises_error(
    tmp_path: Path,
) -> None:
    """Reject a missing feature SQL file."""

    missing_sql = (
        tmp_path / "missing.sql"
    )

    database_path = (
        tmp_path / "warehouse.duckdb"
    )

    database_path.touch()

    with pytest.raises(FileNotFoundError):
        build_churn_feature_dataset(
            database_path=database_path,
            sql_path=missing_sql,
        )