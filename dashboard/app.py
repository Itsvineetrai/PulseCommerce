from pathlib import Path

import duckdb
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
WAREHOUSE_PATH = PROJECT_ROOT / "data" / "warehouse" / "pulsecommerce.duckdb"


st.set_page_config(
    page_title="PulseCommerce Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_data(ttl=60)
def load_overview_data():
    if not WAREHOUSE_PATH.exists():
        raise FileNotFoundError(
            f"Warehouse database not found at: {WAREHOUSE_PATH}"
        )

    con = duckdb.connect(
        str(WAREHOUSE_PATH),
        read_only=True,
    )

    try:
        source_sessions = con.execute(
            """
            SELECT COUNT(DISTINCT session_id)
            FROM analytics_churn_feature_dataset
            """
        ).fetchone()[0]

        churn_rate = con.execute(
            """
            SELECT AVG(churned) * 100
            FROM analytics_churn_feature_dataset
            """
        ).fetchone()[0]

        portfolio_sessions = con.execute(
            """
            SELECT COUNT(*)
            FROM analytics_intervention_portfolio
            """
        ).fetchone()[0]

        roi_summary = con.execute(
            """
            SELECT
                SUM(expected_recovery_value) AS expected_recovery_value,
                SUM(intervention_cost) AS intervention_cost,
                SUM(expected_net_value) AS expected_net_value
            FROM analytics_intervention_roi
            """
        ).fetchone()

        experiment_summary = con.execute(
            """
            SELECT
                variant,
                COUNT(DISTINCT user_id) AS users,
                SUM(
                    CAST(converted AS INTEGER)
                ) AS conversions,
                ROUND(
                    AVG(
                        CAST(converted AS INTEGER)
                    ) * 100,
                    2
                ) AS conversion_rate_pct
            FROM analytics_experiment_population
            GROUP BY variant
            ORDER BY variant
            """
        ).fetchdf()

        intervention_summary = con.execute(
            """
            SELECT
                recommended_action,
                COUNT(*) AS sessions,
                SUM(expected_net_value) AS expected_net_value
            FROM analytics_intervention_portfolio
            GROUP BY recommended_action
            ORDER BY expected_net_value DESC
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

    finally:
        con.close()

    return {
        "source_sessions": source_sessions,
        "churn_rate": churn_rate,
        "portfolio_sessions": portfolio_sessions,
        "expected_recovery_value": roi_summary[0],
        "intervention_cost": roi_summary[1],
        "expected_net_value": roi_summary[2],
        "experiment_summary": experiment_summary,
        "intervention_summary": intervention_summary,
        "risk_distribution": risk_distribution,
    }


def format_currency(value):
    if value is None:
        return "₹0"

    return f"₹{value:,.0f}"


st.title("PulseCommerce Analytics Platform")

st.caption(
    "Product analytics, experimentation, churn intelligence, "
    "and intervention decision analytics."
)

st.divider()

try:
    overview = load_overview_data()

except FileNotFoundError as error:
    st.error(str(error))
    st.stop()

except duckdb.Error as error:
    st.error(f"Unable to read the PulseCommerce warehouse: {error}")
    st.stop()


st.subheader("Executive Overview")

metric_col_1, metric_col_2, metric_col_3, metric_col_4 = st.columns(4)

metric_col_1.metric(
    "Analyzed Sessions",
    f"{overview['source_sessions']:,}",
)

metric_col_2.metric(
    "Churn Rate",
    f"{overview['churn_rate']:.2f}%",
)

metric_col_3.metric(
    "Intervention Portfolio",
    f"{overview['portfolio_sessions']:,} sessions",
)

metric_col_4.metric(
    "Expected Net Value",
    format_currency(overview["expected_net_value"]),
)

st.divider()

st.subheader("Intervention Economics")

value_col_1, value_col_2, value_col_3 = st.columns(3)

value_col_1.metric(
    "Expected Recovery Value",
    format_currency(overview["expected_recovery_value"]),
)

value_col_2.metric(
    "Intervention Cost",
    format_currency(overview["intervention_cost"]),
)

value_col_3.metric(
    "Expected Net Value",
    format_currency(overview["expected_net_value"]),
)

st.divider()

left_column, right_column = st.columns(2)

with left_column:
    st.subheader("Optimized Intervention Portfolio")

    st.dataframe(
        overview["intervention_summary"],
        width="stretch",
        hide_index=True,
    )

with right_column:
    st.subheader("Churn Risk Distribution")

    st.bar_chart(
        overview["risk_distribution"],
        x="risk_band",
        y="sessions",
    )

st.divider()

st.subheader("Experiment Snapshot")

st.dataframe(
    overview["experiment_summary"],
    width="stretch",
    hide_index=True,
)

st.info(
    "Use the pages in the sidebar to explore Funnel & Journey Intelligence, "
    "Experimentation Lab, Customer Intelligence, and the Intervention Center."
)