"""Intervention ROI analysis for PulseCommerce."""

from __future__ import annotations

import pandas as pd


def calculate_intervention_roi(
    portfolio: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate ROI metrics for the intervention portfolio.

    The economics table already contains the expected recovery value
    and intervention cost for every selected session.

    ROI is calculated as:

        expected_net_value
        ------------------
        intervention_cost

    multiplied by 100.

    Sessions with zero intervention cost are assigned an ROI of zero
    because ROI is not applicable when no investment is made.
    """

    roi_dataset = portfolio.copy()

    roi_dataset[
        "roi_pct"
    ] = 0.0

    cost_mask = (
        roi_dataset[
            "intervention_cost"
        ] > 0
    )

    roi_dataset.loc[
        cost_mask,
        "roi_pct",
    ] = (
        roi_dataset.loc[
            cost_mask,
            "expected_net_value",
        ]
        / roi_dataset.loc[
            cost_mask,
            "intervention_cost",
        ]
        * 100
    )

    return roi_dataset