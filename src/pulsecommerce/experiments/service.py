"""Statistical experimentation service for PulseCommerce."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from pathlib import Path

import duckdb
import numpy as np
from scipy.stats import chi2_contingency
from scipy.stats import norm


DEFAULT_DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


@dataclass(frozen=True)
class ExperimentResult:
    """Results of a two-variant conversion experiment."""

    control_users: int
    treatment_users: int

    control_conversions: int
    treatment_conversions: int

    control_conversion_rate: float
    treatment_conversion_rate: float

    absolute_lift: float
    relative_lift: float

    z_statistic: float
    z_test_p_value: float

    chi_square_statistic: float
    chi_square_p_value: float

    confidence_interval_lower: float
    confidence_interval_upper: float

    statistically_significant: bool
    recommendation: str


def analyze_conversion_experiment(
    *,
    database_path: Path = DEFAULT_DATABASE_PATH,
    significance_level: float = 0.05,
    confidence_level: float = 0.95,
) -> ExperimentResult:
    """Analyze Control vs Treatment conversion rates."""

    if not database_path.exists():
        raise FileNotFoundError(
            f"Warehouse database not found: {database_path}"
        )

    if not 0 < significance_level < 1:
        raise ValueError(
            "significance_level must be between 0 and 1."
        )

    if not 0 < confidence_level < 1:
        raise ValueError(
            "confidence_level must be between 0 and 1."
        )

    connection = duckdb.connect(
        str(database_path),
        read_only=True,
    )

    try:
        experiment_data = connection.execute(
            """
            SELECT
                variant,
                COUNT(*) AS users,
                SUM(converted::INTEGER) AS conversions
            FROM analytics_experiment_population
            GROUP BY variant
            ORDER BY variant
            """
        ).fetchdf()

    finally:
        connection.close()

    results = {
        row["variant"]: {
            "users": int(row["users"]),
            "conversions": int(row["conversions"]),
        }
        for _, row in experiment_data.iterrows()
    }

    required_variants = {
        "control",
        "treatment",
    }

    if set(results) != required_variants:
        raise ValueError(
            "Experiment must contain exactly "
            "control and treatment variants."
        )

    control_users = results["control"]["users"]
    treatment_users = results["treatment"]["users"]

    control_conversions = (
        results["control"]["conversions"]
    )
    treatment_conversions = (
        results["treatment"]["conversions"]
    )

    if control_users == 0 or treatment_users == 0:
        raise ValueError(
            "Both variants must contain users."
        )

    control_rate = (
        control_conversions / control_users
    )

    treatment_rate = (
        treatment_conversions / treatment_users
    )

    absolute_lift = (
        treatment_rate - control_rate
    )

    relative_lift = (
        absolute_lift / control_rate
        if control_rate > 0
        else np.nan
    )

    # --------------------------------------------------
    # Two-proportion Z-test
    # --------------------------------------------------

    pooled_rate = (
        control_conversions
        + treatment_conversions
    ) / (
        control_users
        + treatment_users
    )

    pooled_standard_error = sqrt(
        pooled_rate
        * (1 - pooled_rate)
        * (
            (1 / control_users)
            + (1 / treatment_users)
        )
    )

    if pooled_standard_error == 0:
        raise ValueError(
            "Cannot calculate statistical inference "
            "with zero variance."
        )

    z_statistic = (
        absolute_lift
        / pooled_standard_error
    )

    z_test_p_value = (
        2
        * norm.sf(
            abs(z_statistic)
        )
    )

    # --------------------------------------------------
    # Chi-square consistency check
    # --------------------------------------------------

    contingency_table = np.array(
        [
            [
                control_conversions,
                control_users - control_conversions,
            ],
            [
                treatment_conversions,
                treatment_users - treatment_conversions,
            ],
        ]
    )

    (
        chi_square_statistic,
        chi_square_p_value,
        _,
        _,
    ) = chi2_contingency(
        contingency_table,
        correction=False,
    )

    # --------------------------------------------------
    # Confidence interval for conversion difference
    # --------------------------------------------------

    alpha = 1 - confidence_level

    critical_value = norm.ppf(
        1 - alpha / 2
    )

    unpooled_standard_error = sqrt(
        (
            control_rate
            * (1 - control_rate)
            / control_users
        )
        +
        (
            treatment_rate
            * (1 - treatment_rate)
            / treatment_users
        )
    )

    confidence_interval_lower = (
        absolute_lift
        - critical_value
        * unpooled_standard_error
    )

    confidence_interval_upper = (
        absolute_lift
        + critical_value
        * unpooled_standard_error
    )

    statistically_significant = (
        z_test_p_value < significance_level
    )

    if (
        statistically_significant
        and absolute_lift > 0
    ):
        recommendation = (
            "Treatment outperforms Control. "
            "Recommend rollout."
        )

    elif (
        statistically_significant
        and absolute_lift < 0
    ):
        recommendation = (
            "Treatment underperforms Control. "
            "Do not roll out."
        )

    else:
        recommendation = (
            "No statistically significant evidence "
            "of improvement. Continue experiment."
        )

    return ExperimentResult(
        control_users=control_users,
        treatment_users=treatment_users,
        control_conversions=control_conversions,
        treatment_conversions=treatment_conversions,
        control_conversion_rate=control_rate,
        treatment_conversion_rate=treatment_rate,
        absolute_lift=absolute_lift,
        relative_lift=relative_lift,
        z_statistic=z_statistic,
        z_test_p_value=z_test_p_value,
        chi_square_statistic=chi_square_statistic,
        chi_square_p_value=chi_square_p_value,
        confidence_interval_lower=(
            confidence_interval_lower
        ),
        confidence_interval_upper=(
            confidence_interval_upper
        ),
        statistically_significant=(
            statistically_significant
        ),
        recommendation=recommendation,
    )