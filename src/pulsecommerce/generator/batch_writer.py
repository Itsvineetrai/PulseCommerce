"""Parquet micro-batch writer for PulseCommerce events."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


DEFAULT_LANDING_DIRECTORY = Path("data/landing/events")


def write_event_batch(
    events: list[dict[str, Any]],
    batch_number: int,
    output_directory: Path = DEFAULT_LANDING_DIRECTORY,
) -> Path:
    """Write one event micro-batch to a Parquet file.

    Parameters
    ----------
    events:
        Canonical event records to write.
    batch_number:
        Sequential batch identifier.
    output_directory:
        Landing directory for generated Parquet files.

    Returns
    -------
    Path
        Path to the created Parquet file.
    """

    if not events:
        raise ValueError("Cannot write an empty event batch.")

    if batch_number < 1:
        raise ValueError("batch_number must be at least 1.")

    output_directory.mkdir(parents=True, exist_ok=True)

    output_path = (
        output_directory
        / f"batch_{batch_number:06d}.parquet"
    )

    table = pa.Table.from_pylist(events)

    pq.write_table(
        table,
        output_path,
        compression="zstd",
    )

    return output_path