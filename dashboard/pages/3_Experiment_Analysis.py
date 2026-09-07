from pathlib import Path

import duckdb
import plotly.express as px
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[2]
WAREHOUSE_PATH = PROJECT_ROOT / "data" / "warehouse" / "pulsecommerce.duckdb"


st.set_page_config(
    page_title="Experiment Analysis | PulseCommerce",
    page_icon="🧪",
    layout="wide",
)


@st.cache_data(ttl=60)
def load_experiment_data():
    con = duckdb.connect(
        str(WAREHOUSE_PATH),
        read_only=True,
    )

    try:
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

        experiment_population = con.execute(
            """
            SELECT *
            FROM analytics_experiment_population
            """
        ).fetchdf()

    finally:
        con.close()

    return experiment_summary, experiment_population


st.title("Experimentation Lab")

st.caption(
    "Compare experiment variants, conversion outcomes, "
    "and observed treatment performance."
)

if not WAREHOUSE_PATH.exists():
    st.error(f"Warehouse not found: {WAREHOUSE_PATH}")
    st.stop()


try:
    experiment_summary, experiment_population = load_experiment_data()

except duckdb.Error as error:
    st.error(f"Unable to load experiment data: {error}")
    st.stop()


st.divider()

metric_columns = st.columns(len(experiment_summary))

for column, (_, row) in zip(
    metric_columns,
    experiment_summary.iterrows(),
):
    column.metric(
        f"{row['variant'].title()} Conversion",
        f"{row['conversion_rate_pct']:.2f}%",
        f"{int(row['conversions']):,} conversions",
    )

st.divider()

left_column, right_column = st.columns(2)

with left_column:
    conversion_chart = px.bar(
        experiment_summary,
        x="variant",
        y="conversion_rate_pct",
        text="conversion_rate_pct",
        title="Conversion Rate by Variant",
    )

    conversion_chart.update_traces(
        texttemplate="%{text:.2f}%",
        textposition="outside",
    )

    conversion_chart.update_layout(
        xaxis_title="Variant",
        yaxis_title="Conversion Rate (%)",
        showlegend=False,
    )

    st.plotly_chart(
        conversion_chart,
        width="stretch",
    )

with right_column:
    user_chart = px.bar(
        experiment_summary,
        x="variant",
        y="users",
        text="users",
        title="Experiment Population Size",
    )

    user_chart.update_traces(
        texttemplate="%{text:,}",
        textposition="outside",
    )

    user_chart.update_layout(
        xaxis_title="Variant",
        yaxis_title="Users",
        showlegend=False,
    )

    st.plotly_chart(
        user_chart,
        width="stretch",
    )

st.divider()

st.subheader("Experiment Results")

st.dataframe(
    experiment_summary,
    width="stretch",
    hide_index=True,
)

st.divider()

if len(experiment_summary) >= 2:
    control_row = experiment_summary.iloc[0]
    treatment_row = experiment_summary.iloc[1]

    absolute_lift = (
        treatment_row["conversion_rate_pct"]
        - control_row["conversion_rate_pct"]
    )

    if control_row["conversion_rate_pct"] > 0:
        relative_lift = (
            absolute_lift
            / control_row["conversion_rate_pct"]
            * 100
        )
    else:
        relative_lift = 0.0

    lift_col_1, lift_col_2 = st.columns(2)

    lift_col_1.metric(
        "Absolute Lift",
        f"{absolute_lift:.2f} percentage points",
    )

    lift_col_2.metric(
        "Relative Lift",
        f"{relative_lift:.2f}%",
    )

st.divider()

st.subheader("Experiment Population Preview")

st.dataframe(
    experiment_population.head(100),
    width="stretch",
    hide_index=True,
)

st.info(
    "Conversion differences should be interpreted together with "
    "the statistical analysis produced by the experiment pipeline."
)