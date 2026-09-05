"""Phase 1 validation for PulseCommerce synthetic event generation."""

from __future__ import annotations

from pathlib import Path

import duckdb


LANDING_PATH = Path("data/landing/events/*.parquet")


def print_section(title: str) -> None:
    """Print a formatted validation section."""

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


def main() -> None:
    """Run Phase 1 synthetic data validation."""

    if not Path("data/landing/events").exists():
        raise FileNotFoundError(
            "Landing directory does not exist: data/landing/events"
        )

    connection = duckdb.connect()

    connection.execute(
        """
        CREATE VIEW events AS
        SELECT *
        FROM read_parquet('data/landing/events/*.parquet')
        """
    )

    # ---------------------------------------------------------------
    # 1. Dataset overview
    # ---------------------------------------------------------------

    print_section("1. DATASET OVERVIEW")

    overview = connection.execute(
        """
        SELECT
            COUNT(*) AS total_events,
            COUNT(DISTINCT user_id) AS total_users,
            COUNT(DISTINCT session_id) AS total_sessions,
            MIN(event_timestamp) AS first_event,
            MAX(event_timestamp) AS last_event
        FROM events
        """
    ).fetchdf()

    print(overview.to_string(index=False))

    # ---------------------------------------------------------------
    # 2. Event distribution
    # ---------------------------------------------------------------

    print_section("2. EVENT DISTRIBUTION")

    event_distribution = connection.execute(
        """
        SELECT
            event_name,
            COUNT(*) AS event_count
        FROM events
        GROUP BY event_name
        ORDER BY event_count DESC
        """
    ).fetchdf()

    print(event_distribution.to_string(index=False))

    # ---------------------------------------------------------------
    # 3. Persona distribution
    # ---------------------------------------------------------------

    print_section("3. PERSONA DISTRIBUTION")

    personas = connection.execute(
        """
        SELECT
            event_properties.persona AS persona,
            COUNT(DISTINCT user_id) AS users
        FROM events
        WHERE event_name = 'session_start'
        GROUP BY persona
        ORDER BY users DESC
        """
    ).fetchdf()

    print(personas.to_string(index=False))

    # ---------------------------------------------------------------
    # 4. Experiment distribution
    # ---------------------------------------------------------------

    print_section("4. EXPERIMENT DISTRIBUTION")

    experiment_distribution = connection.execute(
        """
        SELECT
            variant,
            COUNT(DISTINCT user_id) AS users,
            ROUND(
                100.0 * COUNT(DISTINCT user_id)
                / SUM(COUNT(DISTINCT user_id)) OVER (),
                2
            ) AS user_percentage
        FROM events
        GROUP BY variant
        ORDER BY variant
        """
    ).fetchdf()

    print(experiment_distribution.to_string(index=False))

    # ---------------------------------------------------------------
    # 5. Funnel
    # ---------------------------------------------------------------

    print_section("5. SESSION FUNNEL")

    funnel = connection.execute(
        """
        WITH session_steps AS (
            SELECT
                session_id,
                MAX(
                    event_name = 'product_view'
                ) AS reached_product,
                MAX(
                    event_name = 'add_to_cart'
                ) AS reached_cart,
                MAX(
                    event_name = 'checkout_start'
                ) AS reached_checkout,
                MAX(
                    event_name = 'purchase_complete'
                ) AS reached_purchase
            FROM events
            GROUP BY session_id
        )
        SELECT
            'product_view' AS funnel_step,
            SUM(reached_product) AS sessions
        FROM session_steps

        UNION ALL

        SELECT
            'add_to_cart',
            SUM(reached_cart)
        FROM session_steps

        UNION ALL

        SELECT
            'checkout_start',
            SUM(reached_checkout)
        FROM session_steps

        UNION ALL

        SELECT
            'purchase_complete',
            SUM(reached_purchase)
        FROM session_steps
        """
    ).fetchdf()

    funnel["conversion_from_product_pct"] = (
        100
        * funnel["sessions"]
        / funnel["sessions"].iloc[0]
    ).round(2)

    print(funnel.to_string(index=False))

    # ---------------------------------------------------------------
    # 6. A/B experiment conversion validation
    # ---------------------------------------------------------------

    print_section("6. CONTROL VS TREATMENT CONVERSION")

    experiment_results = connection.execute(
        """
        WITH session_outcomes AS (
            SELECT
                session_id,
                MAX(variant) AS variant,
                MAX(
                    event_name = 'purchase_complete'
                ) AS converted
            FROM events
            GROUP BY session_id
        )
        SELECT
            variant,
            COUNT(*) AS sessions,
            SUM(converted) AS conversions,
            ROUND(
                100.0 * SUM(converted)
                / COUNT(*),
                3
            ) AS conversion_rate_pct
        FROM session_outcomes
        GROUP BY variant
        ORDER BY variant
        """
    ).fetchdf()

    print(experiment_results.to_string(index=False))

    if len(experiment_results) == 2:
        control_rate = experiment_results.loc[
            experiment_results["variant"] == "control",
            "conversion_rate_pct",
        ].iloc[0]

        treatment_rate = experiment_results.loc[
            experiment_results["variant"] == "treatment",
            "conversion_rate_pct",
        ].iloc[0]

        absolute_lift = treatment_rate - control_rate

        relative_lift = (
            (treatment_rate / control_rate - 1) * 100
            if control_rate > 0
            else 0
        )

        print()
        print(f"Absolute lift: {absolute_lift:.3f} percentage points")
        print(f"Relative lift: {relative_lift:.2f}%")

    # ---------------------------------------------------------------
    # 7. Payment friction validation
    # ---------------------------------------------------------------

    print_section("7. PAYMENT FRICTION BY VARIANT")

    payment_friction = connection.execute(
        """
        SELECT
            variant,
            SUM(
                event_name = 'payment_attempt'
            ) AS payment_attempts,
            SUM(
                event_name = 'payment_error'
            ) AS payment_errors,
            ROUND(
                100.0
                * SUM(event_name = 'payment_error')
                / NULLIF(
                    SUM(event_name = 'payment_attempt'),
                    0
                ),
                3
            ) AS payment_error_rate_pct
        FROM events
        GROUP BY variant
        ORDER BY variant
        """
    ).fetchdf()

    print(payment_friction.to_string(index=False))

    # ---------------------------------------------------------------
    # 8. High-risk cart behavior
    # ---------------------------------------------------------------

    print_section("8. CART IDLE BEHAVIOR BY PERSONA")

    cart_behavior = connection.execute(
        """
        SELECT
            event_properties.persona AS persona,
            COUNT(*) AS sessions
        FROM events
        WHERE event_name = 'session_start'
        GROUP BY persona
        ORDER BY sessions DESC
        """
    ).fetchdf()

    print(cart_behavior.to_string(index=False))

    cart_idle = connection.execute(
        """
        SELECT
            persona,
            ROUND(
                AVG(idle_seconds),
                2
            ) AS average_cart_idle_seconds,
            ROUND(
                MAX(idle_seconds),
                2
            ) AS maximum_cart_idle_seconds
        FROM (
            SELECT
                session_id,
                MAX(
                    CASE
                        WHEN event_name = 'session_start'
                        THEN event_properties.persona
                    END
                ) AS persona,
                MAX(
                    CASE
                        WHEN event_name = 'cart_view'
                        THEN event_properties.idle_before_cart_view_seconds
                    END
                ) AS idle_seconds
            FROM events
            GROUP BY session_id
        )
        WHERE idle_seconds IS NOT NULL
        GROUP BY persona
        ORDER BY average_cart_idle_seconds DESC
        """
    ).fetchdf()

    print(cart_idle.to_string(index=False))

    # ---------------------------------------------------------------
    # 9. Data integrity checks
    # ---------------------------------------------------------------

    print_section("9. DATA INTEGRITY CHECKS")

    duplicate_event_ids = connection.execute(
        """
        SELECT COUNT(*) AS duplicates
        FROM (
            SELECT event_id
            FROM events
            GROUP BY event_id
            HAVING COUNT(*) > 1
        )
        """
    ).fetchone()[0]

    invalid_session_order = connection.execute(
        """
        WITH ordered_events AS (
            SELECT
                session_id,
                event_timestamp,
                LAG(event_timestamp) OVER (
                    PARTITION BY session_id
                    ORDER BY event_timestamp
                ) AS previous_timestamp
            FROM events
        )
        SELECT COUNT(*)
        FROM ordered_events
        WHERE event_timestamp < previous_timestamp
        """
    ).fetchone()[0]

    missing_user_ids = connection.execute(
        """
        SELECT COUNT(*)
        FROM events
        WHERE user_id IS NULL
        """
    ).fetchone()[0]

    missing_session_ids = connection.execute(
        """
        SELECT COUNT(*)
        FROM events
        WHERE session_id IS NULL
        """
    ).fetchone()[0]

    print(f"Duplicate event IDs: {duplicate_event_ids}")
    print(f"Out-of-order session events: {invalid_session_order}")
    print(f"Missing user IDs: {missing_user_ids}")
    print(f"Missing session IDs: {missing_session_ids}")

    print()
    print("=" * 70)
    print("PHASE 1 VALIDATION COMPLETE")
    print("=" * 70)

    connection.close()


if __name__ == "__main__":
    main()