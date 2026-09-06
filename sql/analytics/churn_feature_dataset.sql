CREATE OR REPLACE TABLE analytics_churn_feature_dataset AS

WITH ordered_events AS (
    SELECT
        event_id,
        user_id,
        session_id,
        event_timestamp,
        event_name,
        page,
        device_type,
        traffic_source,
        category,
        quantity,
        price,
        cart_value,

        event_properties.persona AS persona,

        ROW_NUMBER() OVER (
            PARTITION BY session_id
            ORDER BY event_timestamp
        ) AS event_sequence,

        COUNT(*) OVER (
            PARTITION BY session_id
        ) AS total_session_events

    FROM events
),

session_outcomes AS (
    SELECT
        session_id,

        MAX(
            CASE
                WHEN event_name = 'purchase_complete'
                THEN 1
                ELSE 0
            END
        ) AS purchased,

        MIN(
            CASE
                WHEN event_name = 'purchase_complete'
                THEN event_timestamp
            END
        ) AS purchase_timestamp

    FROM ordered_events

    GROUP BY session_id
),

observation_events AS (
    SELECT
        events.*

    FROM ordered_events AS events

    JOIN session_outcomes AS outcomes
        USING (session_id)

    WHERE
        events.event_name NOT IN (
            'purchase_complete',
            'session_end'
        )

        AND (
            outcomes.purchase_timestamp IS NULL
            OR events.event_timestamp
               < outcomes.purchase_timestamp
        )
),

session_observation AS (
    SELECT
        *,

        ROW_NUMBER() OVER (
            PARTITION BY session_id
            ORDER BY event_timestamp DESC
        ) AS reverse_event_sequence

    FROM observation_events
),

observation_cutoff AS (
    SELECT
        *
    FROM session_observation
    WHERE reverse_event_sequence = 1
),

events_before_cutoff AS (
    SELECT
        events.*,

        cutoff.event_timestamp
            AS observation_timestamp

    FROM ordered_events AS events

    JOIN observation_cutoff AS cutoff
        USING (session_id)

    WHERE
        events.event_timestamp
        <= cutoff.event_timestamp
),

session_features AS (
    SELECT
        cutoff.user_id,
        cutoff.session_id,

        cutoff.event_timestamp
            AS observation_timestamp,

        outcomes.purchased,

        COUNT(*) AS total_actions_so_far,

        COUNT(DISTINCT events.event_name)
            AS unique_event_types,

        SUM(
            CASE
                WHEN events.event_name = 'product_view'
                THEN 1
                ELSE 0
            END
        ) AS product_views,

        SUM(
            CASE
                WHEN events.event_name = 'add_to_cart'
                THEN 1
                ELSE 0
            END
        ) AS add_to_cart_actions,

        SUM(
            CASE
                WHEN events.event_name = 'cart_view'
                THEN 1
                ELSE 0
            END
        ) AS cart_views,

        SUM(
            CASE
                WHEN events.event_name = 'checkout_start'
                THEN 1
                ELSE 0
            END
        ) AS checkout_starts,

        SUM(
            CASE
                WHEN events.event_name = 'payment_attempt'
                THEN 1
                ELSE 0
            END
        ) AS payment_attempts,

        SUM(
            CASE
                WHEN events.event_name = 'payment_error'
                THEN 1
                ELSE 0
            END
        ) AS payment_errors,

        MAX(
            CASE
                WHEN events.event_name = 'add_to_cart'
                THEN 1
                ELSE 0
            END
        ) AS has_cart,

        MAX(
            CASE
                WHEN events.event_name = 'checkout_start'
                THEN 1
                ELSE 0
            END
        ) AS reached_checkout,

        MIN(events.event_timestamp)
            AS session_start_timestamp,

        MAX(events.event_timestamp)
            AS latest_event_timestamp,

        ROUND(
            EXTRACT(
                EPOCH FROM
                MAX(events.event_timestamp)
                - MIN(events.event_timestamp)
            ) / 60.0,
            4
        ) AS observed_session_duration_minutes,

        cutoff.device_type,

        cutoff.traffic_source,

        outcomes.purchased

    FROM events_before_cutoff AS events

    JOIN observation_cutoff AS cutoff
        USING (session_id, user_id)

    JOIN session_outcomes AS outcomes
        USING (session_id)

    GROUP BY
        cutoff.user_id,
        cutoff.session_id,
        cutoff.event_timestamp,
        cutoff.device_type,
        cutoff.traffic_source,
        outcomes.purchased
)

SELECT
    user_id,
    session_id,
    observation_timestamp,
    purchased,
    total_actions_so_far,
    unique_event_types,
    product_views,
    add_to_cart_actions,
    cart_views,
    checkout_starts,
    payment_attempts,
    payment_errors,
    has_cart,
    reached_checkout,
    session_start_timestamp,
    latest_event_timestamp,
    observed_session_duration_minutes,
    device_type,
    traffic_source,
    CASE
        WHEN purchased = 1
        THEN 0
        ELSE 1
    END AS churned

FROM session_features;