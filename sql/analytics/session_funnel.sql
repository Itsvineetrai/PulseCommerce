CREATE OR REPLACE TABLE analytics_session_funnel AS

WITH funnel_events AS (
    SELECT
        session_id,
        user_id,
        event_id,
        event_name,
        event_timestamp,

        ROW_NUMBER() OVER (
            PARTITION BY
                session_id,
                event_name
            ORDER BY
                event_timestamp,
                event_id
        ) AS step_rank

    FROM events

    WHERE event_name IN (
        'homepage_view',
        'product_click',
        'add_to_cart',
        'purchase_complete'
    )
),

first_funnel_events AS (
    SELECT
        session_id,
        user_id,
        event_name,
        event_timestamp

    FROM funnel_events

    WHERE step_rank = 1
),

session_steps AS (
    SELECT
        session_id,
        user_id,

        MIN(
            CASE
                WHEN event_name = 'homepage_view'
                THEN event_timestamp
            END
        ) AS homepage_view_at,

        MIN(
            CASE
                WHEN event_name = 'product_click'
                THEN event_timestamp
            END
        ) AS product_click_at,

        MIN(
            CASE
                WHEN event_name = 'add_to_cart'
                THEN event_timestamp
            END
        ) AS add_to_cart_at,

        MIN(
            CASE
                WHEN event_name = 'purchase_complete'
                THEN event_timestamp
            END
        ) AS purchase_complete_at

    FROM first_funnel_events

    GROUP BY
        session_id,
        user_id
)

SELECT
    session_id,
    user_id,

    homepage_view_at,
    product_click_at,
    add_to_cart_at,
    purchase_complete_at,

    homepage_view_at IS NOT NULL
        AS reached_homepage,

    product_click_at IS NOT NULL
        AS reached_product_click,

    add_to_cart_at IS NOT NULL
        AS reached_cart,

    purchase_complete_at IS NOT NULL
        AS reached_purchase,

    CASE
        WHEN purchase_complete_at IS NOT NULL
        THEN 'purchased'

        WHEN add_to_cart_at IS NOT NULL
        THEN 'cart_abandoned'

        WHEN product_click_at IS NOT NULL
        THEN 'product_abandoned'

        ELSE 'homepage_abandoned'
    END AS funnel_outcome

FROM session_steps;