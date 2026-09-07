"""Intervention portfolio and ROI dashboard."""

from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


st.set_page_config(
    page_title="Intervention Portfolio | PulseCommerce",
    layout="wide",
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

WAREHOUSE_PATH = (
    PROJECT_ROOT
    / "data"
    / "warehouse"
    / "pulsecommerce.duckdb"
)


st.title("Intervention Portfolio")
st.caption(
    "Capacity-constrained intervention selection, expected recovery value, "
    "investment cost, and portfolio ROI."
)


@st.cache_data
def load_portfolio_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load intervention portfolio and ROI data from the warehouse."""

    connection = duckdb.connect(
        str(WAREHOUSE_PATH),
        read_only=True,
    )

    portfolio_summary = connection.execute(
        """
        SELECT
            COUNT(*) AS selected_sessions,
            SUM(expected_net_value) AS total_expected_net_value,
            AVG(expected_net_value) AS average_expected_net_value
        FROM analytics_intervention_portfolio
        """
    ).fetchdf()

    action_summary = connection.execute(
        """
        SELECT
            recommended_action,
            COUNT(*) AS sessions,
            SUM(expected_recovery_value) AS expected_recovery_value,
            SUM(intervention_cost) AS intervention_cost,
            SUM(expected_net_value) AS expected_net_value,
            AVG(roi_pct) AS average_roi_pct
        FROM analytics_intervention_roi
        GROUP BY recommended_action
        ORDER BY expected_net_value DESC
        """
    ).fetchdf()

    portfolio_details = connection.execute(
        """
        SELECT
            portfolio_rank,
            session_id,
            recommended_action,
            churn_risk_score,
            cart_value,
            expected_recovery_value,
            intervention_cost,
            expected_net_value,
            roi_pct
        FROM analytics_intervention_roi
        ORDER BY portfolio_rank
        """
    ).fetchdf()

    connection.close()

    return (
        portfolio_summary,
        action_summary,
        portfolio_details,
    )


try:
    (
        portfolio_summary,
        action_summary,
        portfolio_details,
    ) = load_portfolio_data()

except Exception as error:
    st.error(
        f"Unable to read the intervention portfolio data: {error}"
    )
    st.stop()


selected_sessions = int(
    portfolio_summary["selected_sessions"].iloc[0]
)

total_expected_net_value = float(
    portfolio_summary["total_expected_net_value"].iloc[0]
)

average_expected_net_value = float(
    portfolio_summary["average_expected_net_value"].iloc[0]
)

total_expected_recovery_value = float(
    action_summary["expected_recovery_value"].sum()
)

total_intervention_cost = float(
    action_summary["intervention_cost"].sum()
)

portfolio_roi = (
    total_expected_net_value
    / total_intervention_cost
    * 100
    if total_intervention_cost > 0
    else 0
)


st.subheader("Portfolio Investment Summary")

metric_1, metric_2, metric_3, metric_4 = st.columns(4)

metric_1.metric(
    "Selected Sessions",
    f"{selected_sessions:,}",
)

metric_2.metric(
    "Expected Recovery Value",
    f"₹{total_expected_recovery_value:,.2f}",
)

metric_3.metric(
    "Expected Net Value",
    f"₹{total_expected_net_value:,.2f}",
)

metric_4.metric(
    "Portfolio ROI",
    f"{portfolio_roi:,.2f}%",
)


st.divider()

st.subheader("Investment Allocation")

left_column, right_column = st.columns(2)


with left_column:

    action_distribution_chart = px.pie(
        action_summary,
        names="recommended_action",
        values="sessions",
        title="Selected Sessions by Intervention Action",
        hole=0.45,
    )

    st.plotly_chart(
        action_distribution_chart,
        use_container_width=True,
    )


with right_column:

    value_by_action_chart = px.bar(
        action_summary,
        x="recommended_action",
        y="expected_net_value",
        text="expected_net_value",
        title="Expected Net Value by Intervention Action",
        labels={
            "recommended_action": "Intervention Action",
            "expected_net_value": "Expected Net Value",
        },
    )

    value_by_action_chart.update_traces(
        texttemplate="₹%{text:,.0f}",
        textposition="outside",
    )

    value_by_action_chart.update_layout(
        xaxis_title="Intervention Action",
        yaxis_title="Expected Net Value",
    )

    st.plotly_chart(
        value_by_action_chart,
        use_container_width=True,
    )


st.divider()

st.subheader("ROI by Intervention Action")

roi_chart = px.bar(
    action_summary,
    x="recommended_action",
    y="average_roi_pct",
    text="average_roi_pct",
    title="Average ROI by Intervention Action",
    labels={
        "recommended_action": "Intervention Action",
        "average_roi_pct": "Average ROI (%)",
    },
)

roi_chart.update_traces(
    texttemplate="%{text:,.2f}%",
    textposition="outside",
)

roi_chart.update_layout(
    xaxis_title="Intervention Action",
    yaxis_title="Average ROI (%)",
)

st.plotly_chart(
    roi_chart,
    use_container_width=True,
)


st.divider()

st.subheader("Intervention Economics by Action")

action_display = action_summary.copy()

action_display["expected_recovery_value"] = (
    action_display["expected_recovery_value"]
    .round(2)
)

action_display["intervention_cost"] = (
    action_display["intervention_cost"]
    .round(2)
)

action_display["expected_net_value"] = (
    action_display["expected_net_value"]
    .round(2)
)

action_display["average_roi_pct"] = (
    action_display["average_roi_pct"]
    .round(2)
)

st.dataframe(
    action_display,
    use_container_width=True,
    hide_index=True,
)


st.divider()

st.subheader("Top Priority Interventions")

top_interventions = portfolio_details.head(25).copy()

top_interventions["churn_risk_score"] = (
    top_interventions["churn_risk_score"]
    .round(2)
)

top_interventions["cart_value"] = (
    top_interventions["cart_value"]
    .round(2)
)

top_interventions["expected_recovery_value"] = (
    top_interventions["expected_recovery_value"]
    .round(2)
)

top_interventions["intervention_cost"] = (
    top_interventions["intervention_cost"]
    .round(2)
)

top_interventions["expected_net_value"] = (
    top_interventions["expected_net_value"]
    .round(2)
)

top_interventions["roi_pct"] = (
    top_interventions["roi_pct"]
    .round(2)
)

st.dataframe(
    top_interventions,
    use_container_width=True,
    hide_index=True,
)


st.divider()

st.subheader("Portfolio Economics")

st.metric(
    "Average Expected Net Value per Selected Session",
    f"₹{average_expected_net_value:,.2f}",
)

st.caption(
    "The intervention portfolio is capacity-constrained and prioritizes "
    "sessions with the highest expected economic value. ROI is calculated "
    "from the modeled expected net value relative to intervention cost."
)