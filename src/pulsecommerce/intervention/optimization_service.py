"""Intervention portfolio optimization for PulseCommerce."""

from __future__ import annotations

import pandas as pd


DEFAULT_INTERVENTION_CAPACITY = 500


def optimize_intervention_portfolio(
    economics: pd.DataFrame,
    capacity: int = DEFAULT_INTERVENTION_CAPACITY,
) -> pd.DataFrame:
    """Select the highest-value intervention candidates.

    Candidates are ranked by business priority score and selected
    until the available intervention capacity is exhausted.
    """

    if capacity <= 0:
        raise ValueError(
            "Intervention capacity must be greater than zero."
        )

    eligible_candidates = economics[
        economics[
            "recommended_action"
        ].isin(
            [
                "payment_recovery",
                "checkout_recovery",
                "cart_recovery",
            ]
        )
    ].copy()

    ranked_candidates = eligible_candidates.sort_values(
        by=[
            "business_priority_score",
            "expected_net_value",
            "churn_risk_score",
        ],
        ascending=[
            False,
            False,
            False,
        ],
    )

    portfolio = ranked_candidates.head(
        capacity
    ).copy()

    portfolio.insert(
        0,
        "portfolio_rank",
        range(
            1,
            len(portfolio) + 1,
        ),
    )

    return portfolio