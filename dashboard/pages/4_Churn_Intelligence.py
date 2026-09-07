from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WAREHOUSE_PATH = PROJECT_ROOT / "data" / "warehouse" / "pulsecommerce.duckdb"


st.set_page_config(
    page_title="Customer Intelligence | PulseCommerce",
    page_icon="👥",
    layout="wide",
)


@st.cache_data(ttl=60)
def load_customer_data():
    con = duckdb.connect(
        str(WAREHOUSE_PATH),
        read_only=True,
    )

    try:
        risk_distribution = con.execute(
            """
            SELECT
                risk_band,
                COUNT(*) AS sessions,
                ROUND(
                    COUNT(*) * 100.0
                    / SUM(COUNT(*)) OVER (),
                    2
                ) AS percentage
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

        risk_scores = con.execute(
            """
            SELECT
                session_id,
                churn_risk_score,
                risk_band
            FROM analytics_churn_risk_scores
            """
        ).fetchdf()

        churn_features = con.execute(
            """
            SELECT
                device_type,
                traffic_source,
                churned
            FROM analytics_churn_feature_dataset
            """
        ).fetchdf()

        device_analysis = con.execute(
            """
            SELECT
                device_type,
                COUNT(*) AS sessions,
                ROUND(
                    AVG(churned) * 100,
                    2
                ) AS churn_rate_pct
            FROM analytics_churn_feature_dataset
            GROUP BY device_type
            ORDER BY churn_rate_pct DESC
            """
        ).fetchdf()

        traffic_analysis = con.execute(
            """
            SELECT
                traffic_source,
                COUNT(*) AS sessions,
                ROUND(
                    AVG(churned) * 100,
                    2
                ) AS churn_rate_pct
            FROM analytics_churn_feature_dataset
            GROUP BY traffic_source
            ORDER BY churn_rate_pct DESC
            """
        ).fetchdf()

    finally:
        con.close()

    return {
        "risk_distribution": risk_distribution,
        "risk_scores": risk_scores,
        "churn_features": churn_features,
        "device_analysis": device_analysis,
        "traffic_analysis": traffic_analysis,
    }


st.title("Customer Intelligence")

st.caption(
    "Understand churn risk distribution and behavioral differences "
    "across devices and acquisition sources."
)

if not WAREHOUSE_PATH.exists():
    st.error(f"Warehouse not found: {WAREHOUSE_PATH}")
    st.stop()


try:
    data = load_customer_data()

except duckdb.Error as error:
    st.error(f"Unable to load customer intelligence data: {error}")
    st.stop()


st.divider()

risk_distribution = data["risk_distribution"]

total_sessions = int(
    risk_distribution["sessions"].sum()
)

critical_sessions = int(
    risk_distribution.loc[
        risk_distribution["risk_band"] == "critical",
        "sessions",
    ].sum()
)

average_risk = float(
    data["risk_scores"]["churn_risk_score"].mean()
)

metric_col_1, metric_col_2, metric_col_3 = st.columns(3)

metric_col_1.metric(
    "Scored Sessions",
    f"{total_sessions:,}",
)

metric_col_2.metric(
    "Critical Risk Sessions",
    f"{critical_sessions:,}",
)

metric_col_3.metric(
    "Average Churn Risk",
    f"{average_risk:.2f}%",
)

st.divider()

left_column, right_column = st.columns(2)

with left_column:
    risk_chart = px.bar(
        risk_distribution,
        x="risk_band",
        y="sessions",
        text="sessions",
        title="Churn Risk Distribution",
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
    risk_score_chart = px.histogram(
        data["risk_scores"],
        x="churn_risk_score",
        nbins=40,
        title="Churn Risk Score Distribution",
    )

    risk_score_chart.update_layout(
        xaxis_title="Churn Risk Score",
        yaxis_title="Sessions",
        showlegend=False,
    )

    st.plotly_chart(
        risk_score_chart,
        width="stretch",
    )

st.divider()

left_column, right_column = st.columns(2)

with left_column:
    st.subheader("Churn by Device")

    device_chart = px.bar(
        data["device_analysis"],
        x="device_type",
        y="churn_rate_pct",
        text="churn_rate_pct",
        title="Churn Rate by Device",
    )

    device_chart.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    device_chart.update_layout(
        xaxis_title="Device Type",
        yaxis_title="Churn Rate (%)",
        showlegend=False,
    )

    st.plotly_chart(
        device_chart,
        width="stretch",
    )

with right_column:
    st.subheader("Churn by Traffic Source")

    traffic_chart = px.bar(
        data["traffic_analysis"],
        x="traffic_source",
        y="churn_rate_pct",
        text="churn_rate_pct",
        title="Churn Rate by Acquisition Source",
    )

    traffic_chart.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    traffic_chart.update_layout(
        xaxis_title="Traffic Source",
        yaxis_title="Churn Rate (%)",
        showlegend=False,
    )

    st.plotly_chart(
        traffic_chart,
        width="stretch",
    )

st.divider()

st.subheader("Risk Band Summary")

st.dataframe(
    risk_distribution,
    width="stretch",
    hide_index=True,
)

st.divider()

st.subheader("Highest-Risk Sessions")

top_risk_sessions = (
    data["risk_scores"]
    .sort_values(
        "churn_risk_score",
        ascending=False,
    )
    .head(50)
)

st.dataframe(
    top_risk_sessions,
    width="stretch",
    hide_index=True,
)

st.info(
    "The Intervention Center uses these churn scores together with "
    "session behavior and economic value to prioritize recovery actions."
)