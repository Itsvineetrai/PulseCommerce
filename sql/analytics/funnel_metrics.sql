CREATE OR REPLACE TABLE analytics_funnel_metrics AS

WITH funnel_counts AS (
    SELECT
        COUNT(*) AS total_sessions,

        SUM(
            reached_homepage::INTEGER
        ) AS homepage_sessions,

        SUM(
            reached_product_click::INTEGER
        ) AS product_click_sessions,

        SUM(
            reached_cart::INTEGER
        ) AS cart_sessions,

        SUM(
            reached_purchase::INTEGER
        ) AS purchase_sessions

    FROM analytics_session_funnel
),

funnel_rows AS (
    SELECT
        1 AS step_order,
        'homepage_view' AS funnel_step,
        homepage_sessions AS sessions
    FROM funnel_counts

    UNION ALL

    SELECT
        2,
        'product_click',
        product_click_sessions
    FROM funnel_counts

    UNION ALL

    SELECT
        3,
        'add_to_cart',
        cart_sessions
    FROM funnel_counts

    UNION ALL

    SELECT
        4,
        'purchase_complete',
        purchase_sessions
    FROM funnel_counts
),

conversion_metrics AS (
    SELECT
        step_order,
        funnel_step,
        sessions,

        LAG(sessions) OVER (
            ORDER BY step_order
        ) AS previous_step_sessions,

        FIRST_VALUE(sessions) OVER (
            ORDER BY step_order
        ) AS funnel_entry_sessions

    FROM funnel_rows
)

SELECT
    step_order,
    funnel_step,
    sessions,

    ROUND(
        100.0
        * sessions
        / NULLIF(
            funnel_entry_sessions,
            0
        ),
        2
    ) AS absolute_conversion_pct,

    ROUND(
        100.0
        * sessions
        / NULLIF(
            previous_step_sessions,
            0
        ),
        2
    ) AS step_conversion_pct,

    CASE
        WHEN previous_step_sessions IS NULL
        THEN 0

        ELSE previous_step_sessions - sessions
    END AS step_dropoff_sessions,

    CASE
        WHEN previous_step_sessions IS NULL
        THEN 0.0

        ELSE ROUND(
            100.0
            * (
                previous_step_sessions - sessions
            )
            / NULLIF(
                previous_step_sessions,
                0
            ),
            2
        )
    END AS step_dropoff_pct

FROM conversion_metrics

ORDER BY step_order;