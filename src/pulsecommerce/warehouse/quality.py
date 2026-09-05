"""Data quality validation for PulseCommerce events."""

from __future__ import annotations

from dataclasses import dataclass

import duckdb


REQUIRED_COLUMNS = (
    "event_id",
    "user_id",
    "session_id",
    "event_timestamp",
    "event_name",
    "experiment_id",
    "variant",
)

VALID_EVENT_NAMES = (
    "session_start",
    "homepage_view",
    "search",
    "product_view",
    "product_click",
    "wishlist_add",
    "add_to_cart",
    "cart_view",
    "remove_from_cart",
    "checkout_start",
    "payment_attempt",
    "payment_error",
    "purchase_complete",
    "session_end",
)

VALID_VARIANTS = (
    "control",
    "treatment",
)


@dataclass(frozen=True)
class QualityReport:
    """Summary of warehouse data-quality checks."""

    total_rows: int
    duplicate_event_ids: int
    missing_required_values: int
    invalid_event_names: int
    invalid_variants: int
    invalid_timestamps: int

    @property
    def is_valid(self) -> bool:
        """Return True when all quality checks pass."""

        return (
            self.duplicate_event_ids == 0
            and self.missing_required_values == 0
            and self.invalid_event_names == 0
            and self.invalid_variants == 0
            and self.invalid_timestamps == 0
        )


def validate_events(
    connection: duckdb.DuckDBPyConnection,
    relation_name: str,
) -> QualityReport:
    """Validate an event relation against canonical quality rules."""

    total_rows = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {relation_name}
        """
    ).fetchone()[0]

    duplicate_event_ids = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT event_id
            FROM {relation_name}
            GROUP BY event_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    missing_required_values = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {relation_name}
        WHERE
            event_id IS NULL
            OR user_id IS NULL
            OR session_id IS NULL
            OR event_timestamp IS NULL
            OR event_name IS NULL
            OR experiment_id IS NULL
            OR variant IS NULL
        """
    ).fetchone()[0]

    valid_event_names = ", ".join(
        f"'{event_name}'"
        for event_name in VALID_EVENT_NAMES
    )

    invalid_event_names = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {relation_name}
        WHERE event_name NOT IN ({valid_event_names})
        """
    ).fetchone()[0]

    valid_variants = ", ".join(
        f"'{variant}'"
        for variant in VALID_VARIANTS
    )

    invalid_variants = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {relation_name}
        WHERE variant NOT IN ({valid_variants})
        """
    ).fetchone()[0]

    invalid_timestamps = connection.execute(
        f"""
        SELECT COUNT(*)
        FROM {relation_name}
        WHERE event_timestamp IS NULL
        """
    ).fetchone()[0]

    return QualityReport(
        total_rows=total_rows,
        duplicate_event_ids=duplicate_event_ids,
        missing_required_values=missing_required_values,
        invalid_event_names=invalid_event_names,
        invalid_variants=invalid_variants,
        invalid_timestamps=invalid_timestamps,
    )