"""Tests for the churn feature dataset SQL model."""

from __future__ import annotations

from pathlib import Path

import duckdb


def test_churn_feature_dataset_sql(
    tmp_path: Path,
) -> None:
    """Verify churn labels and point-in-time features."""

    database_path = (
        tmp_path / "churn_features.duckdb"
    )

    sql_path = Path(
        "sql/analytics/churn_feature_dataset.sql"
    )

    connection = duckdb.connect(
        str(database_path),
    )

    try:
        connection.execute(
            """
            CREATE TABLE events (
                event_id VARCHAR,
                user_id VARCHAR,
                session_id VARCHAR,
                event_timestamp TIMESTAMP,
                event_name VARCHAR,
                page VARCHAR,
                device_type VARCHAR,
                country VARCHAR,
                traffic_source VARCHAR,
                campaign VARCHAR,
                product_id VARCHAR,
                category VARCHAR,
                quantity BIGINT,
                price DOUBLE,
                cart_value DOUBLE,
                experiment_id VARCHAR,
                variant VARCHAR,
                payment_method VARCHAR,
                error_code VARCHAR,
                event_properties STRUCT(
                    persona VARCHAR,
                    query VARCHAR,
                    idle_before_cart_view_seconds BIGINT
                )
            )
            """
        )

        connection.execute(
            """
            INSERT INTO events VALUES

            (
                'event_1',
                'user_purchase',
                'session_purchase',
                TIMESTAMP '2026-01-01 10:00:00',
                'session_start',
                'homepage',
                'desktop',
                'India',
                'organic',
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                'experiment_1',
                'control',
                NULL,
                NULL,
                {
                    'persona': 'high_intent_buyer',
                    'query': NULL,
                    'idle_before_cart_view_seconds': NULL
                }
            ),

            (
                'event_2',
                'user_purchase',
                'session_purchase',
                TIMESTAMP '2026-01-01 10:01:00',
                'homepage_view',
                'homepage',
                'desktop',
                'India',
                'organic',
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                'experiment_1',
                'control',
                NULL,
                NULL,
                {
                    'persona': NULL,
                    'query': NULL,
                    'idle_before_cart_view_seconds': NULL
                }
            ),

            (
                'event_3',
                'user_purchase',
                'session_purchase',
                TIMESTAMP '2026-01-01 10:02:00',
                'product_view',
                'product',
                'desktop',
                'India',
                'organic',
                NULL,
                'product_1',
                'electronics',
                1,
                100.0,
                NULL,
                'experiment_1',
                'control',
                NULL,
                NULL,
                {
                    'persona': NULL,
                    'query': NULL,
                    'idle_before_cart_view_seconds': NULL
                }
            ),

            (
                'event_4',
                'user_purchase',
                'session_purchase',
                TIMESTAMP '2026-01-01 10:03:00',
                'add_to_cart',
                'cart',
                'desktop',
                'India',
                'organic',
                NULL,
                'product_1',
                'electronics',
                1,
                100.0,
                100.0,
                'experiment_1',
                'control',
                NULL,
                NULL,
                {
                    'persona': NULL,
                    'query': NULL,
                    'idle_before_cart_view_seconds': NULL
                }
            ),

            (
                'event_5',
                'user_purchase',
                'session_purchase',
                TIMESTAMP '2026-01-01 10:05:00',
                'purchase_complete',
                'confirmation',
                'desktop',
                'India',
                'organic',
                NULL,
                'product_1',
                'electronics',
                1,
                100.0,
                100.0,
                'experiment_1',
                'control',
                'card',
                NULL,
                {
                    'persona': NULL,
                    'query': NULL,
                    'idle_before_cart_view_seconds': NULL
                }
            ),

            (
                'event_6',
                'user_purchase',
                'session_purchase',
                TIMESTAMP '2026-01-01 10:06:00',
                'session_end',
                'confirmation',
                'desktop',
                'India',
                'organic',
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                'experiment_1',
                'control',
                NULL,
                NULL,
                {
                    'persona': NULL,
                    'query': NULL,
                    'idle_before_cart_view_seconds': NULL
                }
            ),

            (
                'event_7',
                'user_churn',
                'session_churn',
                TIMESTAMP '2026-01-01 11:00:00',
                'session_start',
                'homepage',
                'mobile',
                'India',
                'paid',
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                'experiment_1',
                'treatment',
                NULL,
                NULL,
                {
                    'persona': 'high_risk_cart',
                    'query': NULL,
                    'idle_before_cart_view_seconds': NULL
                }
            ),

            (
                'event_8',
                'user_churn',
                'session_churn',
                TIMESTAMP '2026-01-01 11:01:00',
                'homepage_view',
                'homepage',
                'mobile',
                'India',
                'paid',
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                'experiment_1',
                'treatment',
                NULL,
                NULL,
                {
                    'persona': NULL,
                    'query': NULL,
                    'idle_before_cart_view_seconds': NULL
                }
            ),

            (
                'event_9',
                'user_churn',
                'session_churn',
                TIMESTAMP '2026-01-01 11:02:00',
                'product_view',
                'product',
                'mobile',
                'India',
                'paid',
                NULL,
                'product_2',
                'fashion',
                1,
                50.0,
                NULL,
                'experiment_1',
                'treatment',
                NULL,
                NULL,
                {
                    'persona': NULL,
                    'query': NULL,
                    'idle_before_cart_view_seconds': NULL
                }
            ),

            (
                'event_10',
                'user_churn',
                'session_churn',
                TIMESTAMP '2026-01-01 11:03:00',
                'add_to_cart',
                'cart',
                'mobile',
                'India',
                'paid',
                NULL,
                'product_2',
                'fashion',
                1,
                50.0,
                50.0,
                'experiment_1',
                'treatment',
                NULL,
                NULL,
                {
                    'persona': NULL,
                    'query': NULL,
                    'idle_before_cart_view_seconds': NULL
                }
            ),

            (
                'event_11',
                'user_churn',
                'session_churn',
                TIMESTAMP '2026-01-01 11:05:00',
                'session_end',
                'cart',
                'mobile',
                'India',
                'paid',
                NULL,
                NULL,
                NULL,
                NULL,
                NULL,
                50.0,
                'experiment_1',
                'treatment',
                NULL,
                NULL,
                {
                    'persona': NULL,
                    'query': NULL,
                    'idle_before_cart_view_seconds': NULL
                }
            )
            """
        )

        sql = sql_path.read_text(
            encoding="utf-8"
        )

        connection.execute(sql)

        results = connection.execute(
            """
            SELECT
                session_id,
                purchased,
                churned,
                total_actions_so_far,
                has_cart
            FROM analytics_churn_feature_dataset
            ORDER BY session_id
            """
        ).fetchall()

    finally:
        connection.close()

    assert results == [
        (
            "session_churn",
            0,
            1,
            4,
            1,
        ),
        (
            "session_purchase",
            1,
            0,
            4,
            1,
        ),
    ]