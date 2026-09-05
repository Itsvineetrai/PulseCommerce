CREATE OR REPLACE TABLE analytics_experiment_population AS

WITH user_experiment_assignment AS (
    SELECT
        user_id,
        MIN(variant) AS variant,
        COUNT(DISTINCT variant) AS variant_count
    FROM events
    WHERE experiment_id IS NOT NULL
    GROUP BY user_id
),

eligible_users AS (
    SELECT DISTINCT
        user_id
    FROM events
    WHERE event_name = 'homepage_view'
),

converted_users AS (
    SELECT DISTINCT
        user_id
    FROM events
    WHERE event_name = 'purchase_complete'
)

SELECT
    assignment.user_id,
    assignment.variant,

    CASE
        WHEN converted.user_id IS NOT NULL
        THEN TRUE
        ELSE FALSE
    END AS converted

FROM user_experiment_assignment AS assignment

JOIN eligible_users AS eligible
    USING (user_id)

LEFT JOIN converted_users AS converted
    USING (user_id)

WHERE assignment.variant_count = 1;