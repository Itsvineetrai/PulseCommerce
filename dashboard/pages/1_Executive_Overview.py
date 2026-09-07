from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WAREHOUSE_PATH = PROJECT_ROOT / "data" / "warehouse" / "pulsecommerce.duckdb"


st.set_page_config(
    page_title="Executive Overview | PulseCommerce",
    page_icon="📈",
    layout="wide",
)


def format_currency(value):
    if value is None:
        return "₹0"

    return f"₹{value:,.0f}"


def format_number(value):
    if value is None:
        return "0"

    return f"{value:,.0f}"


@st.cache_data(ttl=60)
def load_executive_data():
    if not WAREHOUSE_PATH.exists():
        raise FileNotFoundError(
            f"Warehouse database not found at: {WAREHOUSE_PATH}"
        )

    con = duckdb.connect(
        str(WAREHOUSE_PATH),
        read_only=True,
    )

    try:
        overview = con.execute(
            """
            SELECT
                (
                    SELECT COUNT(DISTINCT session_id)
                    FROM analytics_churn_feature_dataset
                ) AS total_sessions,

                (
                    SELECT COUNT(DISTINCT user_id)
                    FROM analytics_churn_feature_dataset
                ) AS total_users,

                (
                    SELECT AVG(churned) * 100
                    FROM analytics_churn_feature_dataset
                ) AS churn_rate_pct,

                (
                    SELECT COUNT(*)
                    FROM analytics_intervention_portfolio
                ) AS portfolio_sessions,

                (
                    SELECT SUM(expected_recovery_value)
                    FROM analytics_intervention_roi
                ) AS expected_recovery_value,

                (
                    SELECT SUM(intervention_cost)
                    FROM analytics_intervention_roi
                ) AS intervention_cost,

                (
                    SELECT SUM(expected_net_value)
                    FROM analytics_intervention_roi
                ) AS expected_net_value
            """
        ).fetchdf()

        risk_distribution = con.execute(
            """
            SELECT
                risk_band,
                COUNT(*) AS sessions
            FROM analytics_churn_risk_scores
            GROUP BY risk_band
            ORDER BY
                CASE risk_band
                    WHEN 'critical' THEN 1
                    WHEN 'high' THEN 2
                    WHEN 'medium' THEN 3
                    WHEN 'low' THEN 4
                    ELSE 5
                END
            """
        ).fetchdf()

        portfolio_summary = con.execute(
            """
            SELECT
                recommended_action,
                COUNT(*) AS sessions,
                SUM(expected_recovery_value) AS expected_recovery_value,
                SUM(intervention_cost) AS intervention_cost,
                SUM(expected_net_value) AS expected_net_value
            FROM analytics_intervention_roi
            GROUP BY recommended_action
            ORDER BY expected_net_value DESC
            """
        ).fetchdf()

        experiment_summary = con.execute(
            """
            SELECT
                variant,
                COUNT(DISTINCT user_id) AS users,
                SUM(CAST(converted AS INTEGER)) AS conversions,
                ROUND(
                    AVG(CAST(converted AS INTEGER)) * 100,
                    2
                ) AS conversion_rate_pct
            FROM analytics_experiment_population
            GROUP BY variant
            ORDER BY variant
            """
        ).fetchdf()

        funnel_metrics = con.execute(
            """
            SELECT *
            FROM analytics_funnel_metrics
            """
        ).fetchdf()

    finally:
        con.close()

    return {
        "overview": overview,
        "risk_distribution": risk_distribution,
        "portfolio_summary": portfolio_summary,
        "experiment_summary": experiment_summary,
        "funnel_metrics": funnel_metrics,
    }


st.title("Executive Overview")

st.caption(
    "A consolidated view of product performance, customer risk, "
    "experimentation, and intervention economics."
)

try:
    data = load_executive_data()

except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

except duckdb.Error as error:
    st.error(f"Unable to read the PulseCommerce warehouse: {error}")
    st.stop()


overview = data["overview"].iloc[0]

st.divider()

metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)

metric_col_1.metric(
    "Total Sessions",
    format_number(overview["total_sessions"]),
)

metric_col_2.metric(
    "Total Users",
    format_number(overview["total_users"]),
)

metric_col_3.metric(
    "Churn Rate",
    f"{overview['churn_rate_pct']:.2f}%",
)

metric_col_4.metric(
    "Optimized Portfolio",
    format_number(overview["portfolio_sessions"]),
)

st.divider()

st.subheader("Business Value")

value_col_1, value_col_2, value_col_3 = st.columns(3)

value_col_1.metric(
    "Expected Recovery Value",
    format_currency(overview["expected_recovery_value"]),
)

value_col_2.metric(
    "Intervention Investment",
    format_currency(overview["intervention_cost"]),
)

value_col_3.metric(
    "Expected Net Value",
    format_currency(overview["expected_net_value"]),
)

st.divider()

left_column, right_column = st.columns(2)

with left_column:
    st.subheader("Customer Risk Distribution")

    risk_chart = px.bar(
        data["risk_distribution"],
        x="risk_band",
        y="sessions",
        text="sessions",
        title="Sessions by Churn Risk Band",
    )

    risk_chart.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
    )

    risk_chart.update_layout(
        xaxis_title="Risk Band",
        yaxis_title="Sessions",
        showlegend=False,
    )

    st.plotly_chart(
        risk_chart,
        width="stretch",
    )

with right_column:
    st.subheader("Portfolio Value by Action")

    portfolio_chart = px.bar(
        data["portfolio_summary"],
        x="recommended_action",
        y="expected_net_value",
        text="expected_net_value",
        title="Expected Net Value by Intervention",
    )

    portfolio_chart.update_traces(
        texttemplate="₹%{text:,.0f}",
        textposition="outside",
    )

    portfolio_chart.update_layout(
        xaxis_title="Recommended Action",
        yaxis_title="Expected Net Value",
        showlegend=False,
    )

    st.plotly_chart(
        portfolio_chart,
        width="stretch",
    )

st.divider()

left_column, right_column = st.columns(2)

with left_column:
    st.subheader("Experiment Performance")

    experiment_chart = px.bar(
        data["experiment_summary"],
        x="variant",
        y="conversion_rate_pct",
        text="conversion_rate_pct",
        title="Conversion Rate by Variant",
    )

    experiment_chart.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    experiment_chart.update_layout(
        xaxis_title="Experiment Variant",
        yaxis_title="Conversion Rate (%)",
        showlegend=False,
    )

    st.plotly_chart(
        experiment_chart,
        width="stretch",
    )

with right_column:
    st.subheader("Intervention Portfolio")

    portfolio_display = data["portfolio_summary"].copy()

    portfolio_display["expected_recovery_value"] = (
        portfolio_display["expected_recovery_value"].map(format_currency)
    )

    portfolio_display["intervention_cost"] = (
        portfolio_display["intervention_cost"].map(format_currency)
    )

    portfolio_display["expected_net_value"] = (
        portfolio_display["expected_net_value"].map(format_currency)
    )

    st.dataframe(
        portfolio_display,
        width="stretch",
        hide_index=True,
    )

st.divider()

st.subheader("Executive Interpretation")

critical_sessions = int(
    data["risk_distribution"]
    .loc[
        data["risk_distribution"]["risk_band"] == "critical",
        "sessions",
    ]
    .sum()
)

st.write(
    f"""
    The platform currently analyzes **{format_number(overview["total_sessions"])} sessions**
    across **{format_number(overview["total_users"])} users**. The observed churn rate is
    **{overview["churn_rate_pct"]:.2f}%**, with **{format_number(critical_sessions)} sessions**
    classified as critical risk.

    The intervention optimization engine selected
    **{format_number(overview["portfolio_sessions"])} sessions** for action and estimates
    **{format_currency(overview["expected_net_value"])}** in net business value after
    intervention costs.
    """
)