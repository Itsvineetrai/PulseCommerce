"""Stable experiment assignment for synthetic users."""

from __future__ import annotations

import hashlib

EXPERIMENT_ID = "EXP-001"

CONTROL = "control"
TREATMENT = "treatment"

VARIANTS = (CONTROL, TREATMENT)


def assign_variant(
    user_id: str,
    experiment_id: str = EXPERIMENT_ID,
) -> str:
    """Assign a user deterministically to an experiment variant.

    The same user and experiment combination always produces
    the same assignment.
    """

    assignment_key = f"{user_id}:{experiment_id}".encode("utf-8")

    digest = hashlib.sha256(assignment_key).digest()

    bucket = int.from_bytes(digest[:8], byteorder="big") % 100

    return CONTROL if bucket < 50 else TREATMENT


def get_experiment_assignment(
    user_id: str,
    experiment_id: str = EXPERIMENT_ID,
) -> dict[str, str]:
    """Return the canonical experiment assignment."""

    return {
        "experiment_id": experiment_id,
        "variant": assign_variant(
            user_id=user_id,
            experiment_id=experiment_id,
        ),
    }