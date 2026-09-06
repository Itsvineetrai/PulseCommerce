"""Business intervention decision logic for PulseCommerce."""

from __future__ import annotations

import pandas as pd


HIGH_PRIORITY_RISK_BANDS = {
    "high",
    "critical",
}


def determine_intervention(
    risk_band: str,
    has_cart: int,
    reached_checkout: int,
    payment_errors: int,
) -> tuple[str, str]:
    """Determine the recommended business intervention."""

    if (
        risk_band in HIGH_PRIORITY_RISK_BANDS
        and payment_errors > 0
        and reached_checkout == 1
    ):
        return (
            "payment_recovery",
            "critical",
        )

    if (
        risk_band in HIGH_PRIORITY_RISK_BANDS
        and reached_checkout == 1
        and payment_errors == 0
    ):
        return (
            "checkout_recovery",
            "high",
        )

    if (
        risk_band in HIGH_PRIORITY_RISK_BANDS
        and has_cart == 1
        and payment_errors == 0
    ):
        return (
            "cart_recovery",
            "high",
        )

    if risk_band == "medium":
        return (
            "monitor",
            "medium",
        )

    return (
        "no_action",
        "low",
    )


def generate_intervention_candidates(
    dataset: pd.DataFrame,
) -> pd.DataFrame:
    """Generate intervention actions for scored sessions."""

    candidates = dataset.copy()

    decisions = candidates.apply(
        lambda row: determine_intervention(
            risk_band=row["risk_band"],
            has_cart=int(row["has_cart"]),
            reached_checkout=int(
                row["reached_checkout"]
            ),
            payment_errors=int(
                row["payment_errors"]
            ),
        ),
        axis=1,
        result_type="expand",
    )

    decisions.columns = [
        "recommended_action",
        "intervention_priority",
    ]

    candidates = pd.concat(
        [
            candidates,
            decisions,
        ],
        axis=1,
    )

    return candidates[
        [
            "user_id",
            "session_id",
            "observation_timestamp",
            "churn_probability",
            "churn_risk_score",
            "risk_band",
            "has_cart",
            "reached_checkout",
            "payment_errors",
            "recommended_action",
            "intervention_priority",
        ]
    ]