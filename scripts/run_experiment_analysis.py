"""Run PulseCommerce A/B experiment analysis."""

from __future__ import annotations

from pulsecommerce.experiments.service import (
    analyze_conversion_experiment,
)


def main() -> None:
    """Run and display experiment statistical inference."""

    print("PulseCommerce A/B Experiment Analysis")
    print("-" * 60)

    result = analyze_conversion_experiment()

    print()
    print("1. EXPERIMENT POPULATION")
    print(
        f"Control users:   {result.control_users:,}"
    )
    print(
        f"Treatment users: {result.treatment_users:,}"
    )

    print()
    print("2. CONVERSIONS")
    print(
        "Control conversions:   "
        f"{result.control_conversions:,}"
    )
    print(
        "Treatment conversions: "
        f"{result.treatment_conversions:,}"
    )

    print()
    print("3. CONVERSION RATES")
    print(
        "Control:   "
        f"{result.control_conversion_rate * 100:.2f}%"
    )
    print(
        "Treatment: "
        f"{result.treatment_conversion_rate * 100:.2f}%"
    )

    print()
    print("4. EXPERIMENT LIFT")
    print(
        "Absolute lift: "
        f"{result.absolute_lift * 100:.2f} "
        "percentage points"
    )
    print(
        "Relative lift: "
        f"{result.relative_lift * 100:.2f}%"
    )

    print()
    print("5. TWO-PROPORTION Z-TEST")
    print(
        f"Z-statistic: {result.z_statistic:.4f}"
    )
    print(
        f"P-value:     {result.z_test_p_value:.6f}"
    )

    print()
    print("6. CHI-SQUARE CONSISTENCY CHECK")
    print(
        "Chi-square statistic: "
        f"{result.chi_square_statistic:.4f}"
    )
    print(
        "P-value:              "
        f"{result.chi_square_p_value:.6f}"
    )

    print()
    print(
        "7. 95% CONFIDENCE INTERVAL "
        "FOR CONVERSION DIFFERENCE"
    )

    print(
        f"Lower bound: "
        f"{result.confidence_interval_lower * 100:.2f} "
        "percentage points"
    )

    print(
        f"Upper bound: "
        f"{result.confidence_interval_upper * 100:.2f} "
        "percentage points"
    )

    print()
    print("8. DECISION")

    significance = (
        "YES"
        if result.statistically_significant
        else "NO"
    )

    print(
        f"Statistically significant: {significance}"
    )
    print(
        f"Recommendation: {result.recommendation}"
    )


if __name__ == "__main__":
    main()