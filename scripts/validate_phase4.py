"""Phase 4 validation for PulseCommerce A/B experimentation."""

from __future__ import annotations

from pathlib import Path

import duckdb

from pulsecommerce.experiments.service import (
    analyze_conversion_experiment,
)


DATABASE_PATH = Path(
    "data/warehouse/pulsecommerce.duckdb"
)


def print_section(title: str) -> None:
    """Print a formatted validation section."""

    print()
    # print("=" * 72)
    print(title)
    # print("=" * 72)


def main() -> None:
    """Validate the Phase 4 experimentation engine."""

    if not DATABASE_PATH.exists():
        raise FileNotFoundError(
            f"Warehouse database not found: {DATABASE_PATH}"
        )

    connection = duckdb.connect(
        str(DATABASE_PATH),
        read_only=True,
    )

    try:
        # -----------------------------------------------------------
        # 1. Experiment population overview
        # -----------------------------------------------------------

        print_section("1. EXPERIMENT POPULATION OVERVIEW")

        population = connection.execute(
            """
            SELECT
                variant,
                COUNT(*) AS users,
                SUM(converted::INTEGER) AS conversions,
                ROUND(
                    100.0
                    * SUM(converted::INTEGER)
                    / COUNT(*),
                    2
                ) AS conversion_rate_pct
            FROM analytics_experiment_population
            GROUP BY variant
            ORDER BY variant
            """
        ).fetchdf()

        print(population.to_string(index=False))

        variants = set(
            population["variant"].tolist()
        )

        if variants != {
            "control",
            "treatment",
        }:
            raise ValueError(
                "Experiment must contain exactly "
                "control and treatment variants."
            )

        # -----------------------------------------------------------
        # 2. User population integrity
        # -----------------------------------------------------------

        print_section("2. USER POPULATION INTEGRITY")

        user_integrity = connection.execute(
            """
            SELECT
                COUNT(*) AS total_rows,
                COUNT(DISTINCT user_id) AS distinct_users,
                COUNT(*) - COUNT(DISTINCT user_id)
                    AS duplicate_users
            FROM analytics_experiment_population
            """
        ).fetchdf()

        print(user_integrity.to_string(index=False))

        duplicate_users = int(
            user_integrity.iloc[0]["duplicate_users"]
        )

        if duplicate_users != 0:
            raise ValueError(
                "Duplicate users found in experiment population."
            )

        # -----------------------------------------------------------
        # 3. Variant assignment integrity
        # -----------------------------------------------------------

        print_section("3. VARIANT ASSIGNMENT INTEGRITY")

        assignment_integrity = connection.execute(
            """
            SELECT
                COUNT(*) AS inconsistent_users
            FROM (
                SELECT
                    user_id
                FROM events
                WHERE experiment_id IS NOT NULL
                GROUP BY user_id
                HAVING COUNT(DISTINCT variant) > 1
            )
            """
        ).fetchdf()

        print(
            assignment_integrity.to_string(
                index=False
            )
        )

        inconsistent_users = int(
            assignment_integrity.iloc[0][
                "inconsistent_users"
            ]
        )

        if inconsistent_users != 0:
            raise ValueError(
                "Inconsistent experiment assignments detected."
            )

        # -----------------------------------------------------------
        # 4. Population reconciliation
        # -----------------------------------------------------------

        print_section("4. POPULATION RECONCILIATION")

        reconciliation = connection.execute(
            """
            SELECT
                (
                    SELECT COUNT(DISTINCT user_id)
                    FROM events
                    WHERE experiment_id IS NOT NULL
                ) AS experiment_assigned_users,

                (
                    SELECT COUNT(*)
                    FROM analytics_experiment_population
                ) AS eligible_population_users
            """
        ).fetchdf()

        print(
            reconciliation.to_string(
                index=False
            )
        )

        assigned_users = int(
            reconciliation.iloc[0][
                "experiment_assigned_users"
            ]
        )

        eligible_users = int(
            reconciliation.iloc[0][
                "eligible_population_users"
            ]
        )

        if eligible_users > assigned_users:
            raise ValueError(
                "Eligible experiment population exceeds "
                "assigned experiment users."
            )

        # -----------------------------------------------------------
        # 5. Conversion count integrity
        # -----------------------------------------------------------

        print_section("5. CONVERSION COUNT INTEGRITY")

        invalid_conversions = connection.execute(
            """
            SELECT
                variant,
                COUNT(*) AS users,
                SUM(converted::INTEGER) AS conversions
            FROM analytics_experiment_population
            GROUP BY variant
            HAVING SUM(converted::INTEGER) > COUNT(*)
            """
        ).fetchdf()

        if invalid_conversions.empty:
            print(
                "Variants with conversions greater than "
                "users: 0"
            )
        else:
            print(
                invalid_conversions.to_string(
                    index=False
                )
            )
            raise ValueError(
                "Conversion counts exceed user counts."
            )

        # -----------------------------------------------------------
        # 6. Statistical inference
        # -----------------------------------------------------------

        print_section("6. STATISTICAL INFERENCE")

        result = analyze_conversion_experiment(
            database_path=DATABASE_PATH
        )

        print(
            "Absolute lift: "
            f"{result.absolute_lift * 100:.2f} "
            "percentage points"
        )

        print(
            "Relative lift: "
            f"{result.relative_lift * 100:.2f}%"
        )

        print(
            "Z-test p-value: "
            f"{result.z_test_p_value:.6f}"
        )

        print(
            "Chi-square p-value: "
            f"{result.chi_square_p_value:.6f}"
        )

        print(
            "95% confidence interval: "
            f"[{result.confidence_interval_lower * 100:.2f}, "
            f"{result.confidence_interval_upper * 100:.2f}] "
            "percentage points"
        )

        print(
            "Statistically significant: "
            f"{result.statistically_significant}"
        )

        print(
            f"Recommendation: {result.recommendation}"
        )

        # -----------------------------------------------------------
        # 7. Statistical decision consistency
        # -----------------------------------------------------------

        print_section("7. STATISTICAL DECISION CONSISTENCY")

        interval_contains_zero = (
            result.confidence_interval_lower
            <= 0
            <= result.confidence_interval_upper
        )

        print(
            "Confidence interval contains zero: "
            f"{interval_contains_zero}"
        )

        if (
            not result.statistically_significant
            and not interval_contains_zero
        ):
            raise ValueError(
                "Non-significant result has a confidence "
                "interval that excludes zero."
            )

        if (
            result.statistically_significant
            and interval_contains_zero
        ):
            raise ValueError(
                "Significant result has a confidence "
                "interval that contains zero."
            )

        # -----------------------------------------------------------
        # Final status
        # -----------------------------------------------------------

        print()
        # print("=" * 72)
        print("PHASE 4 VALIDATION PASSED")
        # print("=" * 72)

    finally:
        connection.close()


if __name__ == "__main__":
    main()