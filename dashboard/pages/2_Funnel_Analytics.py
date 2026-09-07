from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WAREHOUSE_PATH = PROJECT_ROOT / "data" / "warehouse" / "pulsecommerce.duckdb"


st.set_page_config(
    page_title="Funnel Analytics | PulseCommerce",
    page_icon="🔻",
    layout="wide",
)


@st.cache_data(ttl=60)
def load_funnel_data():
    con = duckdb.connect(
        str(WAREHOUSE_PATH),
        read_only=True,
    )

    try:
        funnel_metrics = con.execute(
            """
            SELECT *
            FROM analytics_funnel_metrics
            """
        ).fetchdf()

        velocity_metrics = con.execute(
            """
            SELECT *
            FROM analytics_velocity_metrics
            """
        ).fetchdf()

        session_funnel = con.execute(
            """
            SELECT *
            FROM analytics_session_funnel
            """
        ).fetchdf()

    finally:
        con.close()

    return funnel_metrics, velocity_metrics, session_funnel


st.title("Funnel & Journey Intelligence")

st.caption(
    "Analyze customer progression, conversion bottlenecks, "
    "and behavioral velocity across the purchase journey."
)

if not WAREHOUSE_PATH.exists():
    st.error(f"Warehouse not found: {WAREHOUSE_PATH}")
    st.stop()


try:
    funnel_metrics, velocity_metrics, session_funnel = load_funnel_data()

except duckdb.Error as error:
    st.error(f"Unable to load funnel analytics: {error}")
    st.stop()


st.divider()

st.subheader("Funnel Metrics")

st.dataframe(
    funnel_metrics,
    width="stretch",
    hide_index=True,
)

st.divider()

st.subheader("Session Funnel Distribution")

numeric_columns = session_funnel.select_dtypes(
    include=["number"]
).columns.tolist()

identifier_columns = {
    "session_id",
    "user_id",
}

candidate_columns = [
    column
    for column in numeric_columns
    if column not in identifier_columns
]

if candidate_columns:
    selected_metric = st.selectbox(
        "Select funnel metric",
        candidate_columns,
    )

    distribution_chart = px.histogram(
        session_funnel,
        x=selected_metric,
        nbins=30,
        title=f"Distribution of {selected_metric}",
    )

    distribution_chart.update_layout(
        xaxis_title=selected_metric,
        yaxis_title="Sessions",
        showlegend=False,
    )

    st.plotly_chart(
        distribution_chart,
        width="stretch",
    )
else:
    st.info(
        "No numeric session-level funnel metrics were available "
        "for distribution analysis."
    )

st.divider()

st.subheader("Behavioral Velocity")

st.dataframe(
    velocity_metrics,
    width="stretch",
    hide_index=True,
)

velocity_numeric_columns = velocity_metrics.select_dtypes(
    include=["number"]
).columns.tolist()

if velocity_numeric_columns:
    selected_velocity_metric = st.selectbox(
        "Select velocity metric",
        velocity_numeric_columns,
        key="velocity_metric",
    )

    velocity_chart = px.bar(
        velocity_metrics,
        x=velocity_metrics.columns[0],
        y=selected_velocity_metric,
        title=f"Behavioral Velocity: {selected_velocity_metric}",
    )

    velocity_chart.update_layout(
        xaxis_title=velocity_metrics.columns[0],
        yaxis_title=selected_velocity_metric,
        showlegend=False,
    )

    st.plotly_chart(
        velocity_chart,
        width="stretch",
    )

st.divider()

st.subheader("Journey Dataset Preview")

st.dataframe(
    session_funnel.head(100),
    width="stretch",
    hide_index=True,
)

st.info(
    "Use this page to identify where users stop progressing "
    "through the journey and which behavioral patterns are "
    "associated with slower progression."
)