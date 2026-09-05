"""Phase 3 validation for PulseCommerce behavioral analytics."""

from __future__ import annotations

from pathlib import Path

import duckdb


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
    """Validate Phase 3 behavioral analytics."""

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
        # 1. Analytics table existence
        # -----------------------------------------------------------

        print_section("1. ANALYTICS TABLES")

        tables = connection.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'main'
              AND table_name LIKE 'analytics_%'
            ORDER BY table_name
            """
        ).fetchdf()

        print(tables.to_string(index=False))

        required_tables = {
            "analytics_session_funnel",
            "analytics_funnel_metrics",
            "analytics_velocity_metrics",
        }

        existing_tables = set(
            tables["table_name"].tolist()
        )

        missing_tables = (
            required_tables - existing_tables
        )

        if missing_tables:
            raise ValueError(
                f"Missing analytics tables: {missing_tables}"
            )

        # -----------------------------------------------------------
        # 2. Primary funnel metrics
        # -----------------------------------------------------------

        print_section("2. PRIMARY FUNNEL METRICS")

        funnel_metrics = connection.execute(
            """
            SELECT
                step_order,
                funnel_step,
                sessions,
                absolute_conversion_pct,
                step_conversion_pct,
                step_dropoff_sessions,
                step_dropoff_pct
            FROM analytics_funnel_metrics
            ORDER BY step_order
            """
        ).fetchdf()

        print(funnel_metrics.to_string(index=False))

        # -----------------------------------------------------------
        # 3. Funnel outcome distribution
        # -----------------------------------------------------------

        print_section("3. FUNNEL OUTCOME DISTRIBUTION")

        outcomes = connection.execute(
            """
            SELECT
                funnel_outcome,
                COUNT(*) AS sessions,
                ROUND(
                    100.0 * COUNT(*)
                    / SUM(COUNT(*)) OVER (),
                    2
                ) AS percentage
            FROM analytics_session_funnel
            GROUP BY funnel_outcome
            ORDER BY sessions DESC
            """
        ).fetchdf()

        print(outcomes.to_string(index=False))

        # -----------------------------------------------------------
        # 4. Funnel event ordering
        # -----------------------------------------------------------

        print_section("4. FUNNEL ORDERING INTEGRITY")

        ordering = connection.execute(
            """
            SELECT
                COUNT(*) FILTER (
                    WHERE
                        product_click_at IS NOT NULL
                        AND homepage_view_at IS NOT NULL
                        AND product_click_at < homepage_view_at
                ) AS invalid_product_click_order,

                COUNT(*) FILTER (
                    WHERE
                        add_to_cart_at IS NOT NULL
                        AND product_click_at IS NOT NULL
                        AND add_to_cart_at < product_click_at
                ) AS invalid_cart_order,

                COUNT(*) FILTER (
                    WHERE
                        purchase_complete_at IS NOT NULL
                        AND add_to_cart_at IS NOT NULL
                        AND purchase_complete_at < add_to_cart_at
                ) AS invalid_purchase_order

            FROM analytics_session_funnel
            """
        ).fetchdf()

        print(ordering.to_string(index=False))

        ordering_values = ordering.iloc[0]

        if any(
            ordering_values[column] != 0
            for column in ordering.columns
        ):
            raise ValueError(
                "Funnel ordering integrity check failed."
            )

        # -----------------------------------------------------------
        # 5. Conversion consistency
        # -----------------------------------------------------------

        print_section("5. PURCHASE CONSISTENCY")

        consistency = connection.execute(
            """
            SELECT
                (
                    SELECT COUNT(*)
                    FROM events
                    WHERE event_name = 'purchase_complete'
                ) AS raw_purchase_events,

                (
                    SELECT COUNT(*)
                    FROM analytics_session_funnel
                    WHERE reached_purchase
                ) AS funnel_purchase_sessions
            """
        ).fetchdf()

        print(consistency.to_string(index=False))

        # -----------------------------------------------------------
        # 6. Session velocity overview
        # -----------------------------------------------------------

        print_section("6. SESSION VELOCITY OVERVIEW")

        velocity = connection.execute(
            """
            SELECT
                COUNT(*) AS sessions,
                ROUND(
                    AVG(session_duration_minutes),
                    2
                ) AS avg_session_duration_minutes,
                ROUND(
                    AVG(average_event_gap_minutes),
                    2
                ) AS avg_event_gap_minutes,
                ROUND(
                    AVG(maximum_event_gap_minutes),
                    2
                ) AS avg_max_event_gap_minutes,
                ROUND(
                    AVG(total_events),
                    2
                ) AS avg_events_per_session
            FROM analytics_velocity_metrics
            """
        ).fetchdf()

        print(velocity.to_string(index=False))

        # -----------------------------------------------------------
        # 7. Purchased vs cart abandoned behavior
        # -----------------------------------------------------------

        print_section(
            "7. PURCHASED VS CART-ABANDONED VELOCITY"
        )

        behavioral_comparison = connection.execute(
            """
            SELECT
                funnel.funnel_outcome,

                COUNT(*) AS sessions,

                ROUND(
                    AVG(
                        velocity.session_duration_minutes
                    ),
                    2
                ) AS avg_session_duration_minutes,

                ROUND(
                    AVG(
                        velocity.average_event_gap_minutes
                    ),
                    2
                ) AS avg_event_gap_minutes,

                ROUND(
                    AVG(
                        velocity.maximum_event_gap_minutes
                    ),
                    2
                ) AS avg_max_event_gap_minutes,

                ROUND(
                    AVG(velocity.total_events),
                    2
                ) AS avg_events_per_session

            FROM analytics_session_funnel AS funnel

            JOIN analytics_velocity_metrics AS velocity
                USING (session_id, user_id)

            WHERE funnel.funnel_outcome IN (
                'purchased',
                'cart_abandoned'
            )

            GROUP BY funnel.funnel_outcome

            ORDER BY funnel.funnel_outcome
            """
        ).fetchdf()

        print(
            behavioral_comparison.to_string(
                index=False
            )
        )

        # -----------------------------------------------------------
        # 8. Cart dwell / idle analysis
        # -----------------------------------------------------------

        print_section("8. CART IDLE ANALYSIS")

        cart_idle = connection.execute(
        """
            WITH session_personas AS (
                SELECT
                    session_id,
                    user_id,
                    event_properties.persona AS persona
                FROM events
                WHERE event_name = 'session_start'
            )

            SELECT
                personas.persona,

                COUNT(*) AS cart_view_events,

                ROUND(
                AVG(
                    cart_events.event_properties
                        .idle_before_cart_view_seconds
                ),  
                2
                ) AS avg_idle_seconds,

                ROUND(
                    MAX(
                        cart_events.event_properties
                            .idle_before_cart_view_seconds
                    ),
                    2
                ) AS max_idle_seconds

            FROM events AS cart_events

            JOIN session_personas AS personas
                USING (session_id, user_id)

            WHERE cart_events.event_name = 'cart_view'
                AND cart_events.event_properties
                    .idle_before_cart_view_seconds
                    IS NOT NULL

            GROUP BY personas.persona

            ORDER BY avg_idle_seconds DESC
            """
        ).fetchdf()

        print(cart_idle.to_string(index=False))

        # -----------------------------------------------------------
        # 9. Final status
        # -----------------------------------------------------------

        print()
        # print("=" * 72)
        print("PHASE 3 VALIDATION PASSED")
        # print("=" * 72)

    finally:
        connection.close()


if __name__ == "__main__":
    main()