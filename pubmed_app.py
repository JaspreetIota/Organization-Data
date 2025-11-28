import streamlit as st
import pandas as pd
import json
from streamlit_echarts import st_echarts

st.set_page_config(layout="wide")
st.title("Flexible Multi-Chart Dashboard (Cloud Compatible)")

# ---------------------------
# Upload Excel
# ---------------------------
uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
if uploaded_file:
    df = pd.read_excel(uploaded_file)
    st.subheader("Data Preview")
    st.dataframe(df)

    # ---------------------------
    # Dashboard management
    # ---------------------------
    dashboard_name = st.text_input("Dashboard Name", value="default_dashboard")
    
    # Load saved dashboards
    try:
        with open("dashboards.json", "r") as f:
            dashboards = json.load(f)
    except FileNotFoundError:
        dashboards = {}

    if st.button("Save Dashboard"):
        dashboards[dashboard_name] = []  # Will store chart configs
        with open("dashboards.json", "w") as f:
            json.dump(dashboards, f)
        st.success(f"Dashboard '{dashboard_name}' saved!")

    if dashboards:
        st.sidebar.subheader("Saved Dashboards")
        selected_dashboard = st.sidebar.selectbox("Select Dashboard", list(dashboards.keys()))
        if selected_dashboard:
            st.sidebar.write(f"Dashboard: {selected_dashboard}")

    # ---------------------------
    # Add new chart
    # ---------------------------
    st.subheader("Add Chart")
    columns = df.columns.tolist()
    x_axis = st.selectbox("X-axis Column", options=columns, key="x_col")
    chart_type = st.selectbox(
        "Chart Type",
        ["Bar", "Line", "Pie", "Scatter", "Area", "Funnel", "Radar"],
        key="chart_type"
    )

    # ---------------------------
    # Prepare data (Y-axis is always count)
    # ---------------------------
    counts = df[x_axis].value_counts()
    x_data = counts.index.tolist()
    y_data = counts.values.tolist()

    # ---------------------------
    # Build chart options dynamically
    # ---------------------------
    if chart_type == "Bar":
        options = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value"},
            "series": [{"data": y_data, "type": "bar"}]
        }
    elif chart_type == "Line":
        options = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value"},
            "series": [{"data": y_data, "type": "line", "smooth": True}]
        }
    elif chart_type == "Pie":
        options = {
            "tooltip": {"trigger": "item"},
            "series": [{
                "type": "pie",
                "radius": "60%",
                "data": [{"value": v, "name": str(n)} for n, v in zip(x_data, y_data)]
            }]
        }
    elif chart_type == "Scatter":
        options = {
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value"},
            "series": [{"data": [[x_data[i], y_data[i]] for i in range(len(x_data))], "type": "scatter"}]
        }
    elif chart_type == "Area":
        options = {
            "tooltip": {"trigger": "axis"},
            "xAxis": {"type": "category", "data": x_data},
            "yAxis": {"type": "value"},
            "series": [{"data": y_data, "type": "line", "areaStyle": {}}]
        }
    elif chart_type == "Funnel":
        options = {
            "tooltip": {"trigger": "item"},
            "series": [{"type": "funnel", "data": [{"value": v, "name": str(n)} for n, v in zip(x_data, y_data)]}]
        }
    elif chart_type == "Radar":
        options = {
            "tooltip": {},
            "radar": {
                "indicator": [{"name": str(n), "max": max(y_data) + 5} for n in x_data]
            },
            "series": [{"type": "radar", "data": [{"value": y_data, "name": "Count"}]}]
        }

    # ---------------------------
    # Layout multiple charts
    # ---------------------------
    num_charts = st.number_input("Charts per row", min_value=1, max_value=4, value=2)
    cols = st.columns(num_charts)
    for i, col in enumerate(cols):
        with col:
            st_echarts(options=options, height="400px")
