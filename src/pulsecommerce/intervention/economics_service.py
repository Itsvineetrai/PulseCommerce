"""Intervention economics for PulseCommerce."""

from __future__ import annotations

import pandas as pd


# Explicit business assumptions.
# These values are configurable assumptions and are not ML predictions.
#
# recovery_probability represents the assumed probability that an
# intervention successfully recovers an at-risk session.

ACTION_ASSUMPTIONS = {
    "payment_recovery": {
        "recovery_probability": 0.35,
        "intervention_cost": 8.0,
    },
    "checkout_recovery": {
        "recovery_probability": 0.20,
        "intervention_cost": 5.0,
    },
    "cart_recovery": {
        "recovery_probability": 0.12,
        "intervention_cost": 3.0,
    },
    "monitor": {
        "recovery_probability": 0.0,
        "intervention_cost": 0.0,
    },
    "no_action": {
        "recovery_probability": 0.0,
        "intervention_cost": 0.0,
    },
}


def calculate_intervention_economics(
    dataset: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate expected economic value for intervention candidates.

    Expected recovery value:

        cart_value
        × churn_probability
        × intervention_recovery_probability

    Expected net value:

        expected_recovery_value
        − intervention_cost

    Business priority score:

        max(expected_net_value, 0)
    """

    economics = dataset.copy()

    economics["recovery_probability"] = economics[
        "recommended_action"
    ].map(
        lambda action: ACTION_ASSUMPTIONS[action][
            "recovery_probability"
        ]
    )

    economics["intervention_cost"] = economics[
        "recommended_action"
    ].map(
        lambda action: ACTION_ASSUMPTIONS[action][
            "intervention_cost"
        ]
    )

    economics["expected_recovery_value"] = (
        economics["cart_value"]
        * economics["churn_probability"]
        * economics["recovery_probability"]
    )

    economics["expected_net_value"] = (
        economics["expected_recovery_value"]
        - economics["intervention_cost"]
    )

    economics["business_priority_score"] = economics[
        "expected_net_value"
    ].clip(
        lower=0
    )

    return economics[
        [
            "user_id",
            "session_id",
            "observation_timestamp",
            "recommended_action",
            "intervention_priority",
            "risk_band",
            "churn_probability",
            "churn_risk_score",
            "cart_value",
            "recovery_probability",
            "intervention_cost",
            "expected_recovery_value",
            "expected_net_value",
            "business_priority_score",
        ]
    ]