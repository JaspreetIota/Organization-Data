import streamlit as st
import pandas as pd
from streamlit_echarts import st_echarts

st.title("Superset-Style ECharts in Streamlit")
st.write("Upload an Excel file and create interactive charts with ECharts.")

uploaded = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded:
    df = pd.read_excel(uploaded)
    st.write("### Data Preview", df)

    columns = df.columns.tolist()
    x_axis = st.selectbox("X-axis Column", options=columns)
    y_axis = st.selectbox("Y-axis Column (numeric)", options=df.select_dtypes(include="number").columns)

    chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Pie"])

    # Build ECharts options based on type
    if chart_type == "Bar":
        options = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": df[x_axis].astype(str).tolist()},
            "yAxis": {"type": "value"},
            "series": [{
                "data": df[y_axis].tolist(),
                "type": "bar",
                "smooth": True,
            }]
        }

    elif chart_type == "Line":
        options = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": df[x_axis].astype(str).tolist()},
            "yAxis": {"type": "value"},
            "series": [{
                "data": df[y_axis].tolist(),
                "type": "line",
                "smooth": True,
            }]
        }

    elif chart_type == "Pie":
        options = {
            "tooltip": {"trigger": "item"},
            "series": [{
                "type": "pie",
                "radius": "60%",
                "data": [
                    {"value": v, "name": str(n)}
                    for n, v in zip(df[x_axis], df[y_axis])
                ],
            }]
        }

    st_echarts(options=options, height="500px")
