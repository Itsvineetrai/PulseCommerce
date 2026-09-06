"""Feature configuration for PulseCommerce ML models."""

from __future__ import annotations


TARGET_COLUMN = "churned"


NUMERIC_FEATURES = [
    "total_actions_so_far",
    "unique_event_types",
    "product_views",
    "add_to_cart_actions",
    "cart_views",
    "checkout_starts",
    "payment_attempts",
    "payment_errors",
    "observed_session_duration_minutes",
]


CATEGORICAL_FEATURES = [
    "device_type",
    "traffic_source",
]


FEATURE_COLUMNS = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)


EXCLUDED_COLUMNS = [
    "user_id",
    "session_id",
    "observation_timestamp",
    "session_start_timestamp",
    "latest_event_timestamp",
    "purchased",
    "churned",
]