CREATE OR REPLACE TABLE analytics_velocity_metrics AS

WITH ordered_events AS (
    SELECT
        session_id,
        user_id,
        event_id,
        event_name,
        event_timestamp,

        LAG(event_timestamp) OVER (
            PARTITION BY session_id
            ORDER BY
                event_timestamp,
                event_id
        ) AS previous_event_timestamp,

        LAG(event_name) OVER (
            PARTITION BY session_id
            ORDER BY
                event_timestamp,
                event_id
        ) AS previous_event_name,

        LEAD(event_timestamp) OVER (
            PARTITION BY session_id
            ORDER BY
                event_timestamp,
                event_id
        ) AS next_event_timestamp,

        LEAD(event_name) OVER (
            PARTITION BY session_id
            ORDER BY
                event_timestamp,
                event_id
        ) AS next_event_name

    FROM events
),

event_velocity AS (
    SELECT
        session_id,
        user_id,
        event_name,
        event_timestamp,
        previous_event_name,
        next_event_name,

        ROUND(
            EPOCH(
                event_timestamp
                - previous_event_timestamp
            ) / 60.0,
            2
        ) AS minutes_since_previous_event,

        ROUND(
            EPOCH(
                next_event_timestamp
                - event_timestamp
            ) / 60.0,
            2
        ) AS minutes_to_next_event

    FROM ordered_events
),

session_velocity AS (
    SELECT
        session_id,
        user_id,

        AVG(
            minutes_since_previous_event
        ) AS average_event_gap_minutes,

        MAX(
            minutes_since_previous_event
        ) AS maximum_event_gap_minutes,

        AVG(
            minutes_to_next_event
        ) AS average_next_event_gap_minutes,

        COUNT(*) AS total_events,

        MIN(event_timestamp) AS session_start_at,
        MAX(event_timestamp) AS session_end_at

    FROM event_velocity

    GROUP BY
        session_id,
        user_id
)

SELECT
    session_id,
    user_id,

    total_events,

    ROUND(
        EPOCH(
            session_end_at
            - session_start_at
        ) / 60.0,
        2
    ) AS session_duration_minutes,

    ROUND(
        average_event_gap_minutes,
        2
    ) AS average_event_gap_minutes,

    ROUND(
        maximum_event_gap_minutes,
        2
    ) AS maximum_event_gap_minutes,

    ROUND(
        average_next_event_gap_minutes,
        2
    ) AS average_next_event_gap_minutes

FROM session_velocity;