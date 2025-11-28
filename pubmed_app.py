import streamlit as st
import pandas as pd
import numpy as np
import json
import os
from streamlit_echarts import st_echarts

st.set_page_config(layout="wide")
st.title("Persistent Multi-Chart Dashboard Builder")

# ---------------------------
# File upload for new dataset
# ---------------------------
uploaded_file = st.file_uploader("Upload Excel/CSV", type=["xlsx","csv"], key="file_upload")

if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    df = df.replace([np.nan, np.inf, -np.inf], None)
    st.subheader("Data Preview")
    st.dataframe(df)
    columns = df.columns.tolist()

    # ---------------------------
    # Persistent dashboards storage
    # ---------------------------
    dashboards_file = "dashboards.json"
    if not os.path.exists(dashboards_file):
        with open(dashboards_file, "w") as f:
            json.dump({}, f)

    with open(dashboards_file, "r") as f:
        dashboards = json.load(f)

    # ---------------------------
    # Select or create dashboard
    # ---------------------------
    st.sidebar.subheader("Dashboards")
    dashboard_name = st.sidebar.text_input("Dashboard Name", value="default_dashboard")

    # Delete a dashboard
    if st.sidebar.button("Delete Dashboard") and dashboard_name in dashboards:
        del dashboards[dashboard_name]
        with open(dashboards_file, "w") as f:
            json.dump(dashboards, f)
        st.sidebar.success(f"Dashboard '{dashboard_name}' deleted!")
        st.session_state.dashboard = []

    # Load dashboard into session state
    if "dashboard" not in st.session_state:
        st.session_state.dashboard = dashboards.get(dashboard_name, [])

    if st.sidebar.button("Save Dashboard"):
        dashboards[dashboard_name] = st.session_state.dashboard
        with open(dashboards_file, "w") as f:
            json.dump(dashboards, f)
        st.sidebar.success(f"Dashboard '{dashboard_name}' saved!")

    # Show list of saved dashboards
    if dashboards:
        st.sidebar.subheader("Load Dashboard")
        selected_dashboard = st.sidebar.selectbox("Select Dashboard", list(dashboards.keys()))
        if st.sidebar.button("Load Selected Dashboard") and selected_dashboard in dashboards:
            st.session_state.dashboard = dashboards[selected_dashboard]
            st.sidebar.success(f"Dashboard '{selected_dashboard}' loaded!")

    # ---------------------------
    # Add new chart
    # ---------------------------
    st.subheader("Add Chart")
    x_axis = st.selectbox("X-axis Column", options=columns, key="x_col")
    y_axis = st.selectbox("Y-axis (numeric or <count>)", options=["<count>"] + columns, key="y_col")
    chart_type = st.selectbox(
        "Chart Type",
        ["Bar", "Stacked Bar", "Horizontal Bar", "Line", "Area", "Stacked Area",
         "Pie", "Donut", "Scatter", "Radar", "Funnel", "Gauge", "Treemap", "Word Cloud"],
        key="chart_type"
    )
    width = st.slider("Width (columns)", 2, 12, 6)
    height = st.slider("Height (pixels)", 200, 800, 400)

    if st.button("Add Chart"):
        st.session_state.dashboard.append({
            "x_axis": x_axis,
            "y_axis": y_axis,
            "type": chart_type,
            "width": width,
            "height": height
        })

    st.write("---")
    st.subheader("Your Dashboard")

    # ---------------------------
    # Render all charts safely
    # ---------------------------
    charts_per_row = st.number_input("Charts per row", min_value=1, max_value=4, value=2)

    for i in range(0, len(st.session_state.dashboard), charts_per_row):
        cols = st.columns(charts_per_row)
        for j, chart in enumerate(st.session_state.dashboard[i:i+charts_per_row]):
            with cols[j]:
                # Delete individual chart
                if st.button(f"Delete Chart {i+j+1}"):
                    st.session_state.dashboard.pop(i+j)
                    st.experimental_rerun()

                # Skip chart if columns are missing
                if chart["x_axis"] not in df.columns or (chart["y_axis"] not in df.columns and chart["y_axis"] != "<count>"):
                    st.error(f"Chart columns no longer exist: X='{chart['x_axis']}', Y='{chart['y_axis']}'")
                    continue

                # Prepare chart data
                x_data = df[chart["x_axis"]].astype(str)
                if chart["y_axis"] == "<count>":
                    counted = x_data.value_counts().reset_index()
                    counted.columns = [chart["x_axis"], "count"]
                    x_list = counted[chart["x_axis"]].tolist()
                    y_list = counted["count"].tolist()
                else:
                    if pd.api.types.is_numeric_dtype(df[chart["y_axis"]]):
                        y_list = df[chart["y_axis"]].replace([np.nan, np.inf, -np.inf], None).tolist()
                        x_list = x_data.tolist()
                    else:
                        counted = df[chart["y_axis"]].astype(str).value_counts().reset_index()
                        counted.columns = [chart["y_axis"], "count"]
                        x_list = counted[chart["y_axis"]].tolist()
                        y_list = counted["count"].tolist()

                # Build chart options
                options = {}
                if chart["type"] == "Bar":
                    options = {"tooltip":{"trigger":"axis"}, "xAxis":{"type":"category","data":x_list}, "yAxis":{"type":"value"}, "series":[{"data":y_list,"type":"bar"}]}
                elif chart["type"] == "Stacked Bar":
                    options = {"tooltip":{"trigger":"axis"}, "xAxis":{"type":"category","data":x_list}, "yAxis":{"type":"value"}, "series":[{"data":y_list,"type":"bar","stack":"total"}]}
                elif chart["type"] == "Horizontal Bar":
                    options = {"tooltip":{"trigger":"axis"}, "xAxis":{"type":"value"}, "yAxis":{"type":"category","data":x_list}, "series":[{"data":y_list,"type":"bar"}]}
                elif chart["type"] == "Line":
                    options = {"tooltip":{"trigger":"axis"}, "xAxis":{"type":"category","data":x_list}, "yAxis":{"type":"value"}, "series":[{"data":y_list,"type":"line"}]}
                elif chart["type"] == "Area":
                    options = {"tooltip":{"trigger":"axis"}, "xAxis":{"type":"category","data":x_list}, "yAxis":{"type":"value"}, "series":[{"data":y_list,"type":"line","areaStyle":{}}]}
                elif chart["type"] == "Stacked Area":
                    options = {"tooltip":{"trigger":"axis"}, "xAxis":{"type":"category","data":x_list}, "yAxis":{"type":"value"}, "series":[{"data":y_list,"type":"line","areaStyle":{},"stack":"total"}]}
                elif chart["type"] == "Pie":
                    options = {"tooltip":{"trigger":"item"}, "series":[{"type":"pie","radius":"60%","data":[{"value":v,"name":n} for n,v in zip(x_list,y_list)]}]}
                elif chart["type"] == "Donut":
                    options = {"tooltip":{"trigger":"item"}, "series":[{"type":"pie","radius":["40%","70%"],"data":[{"value":v,"name":n} for n,v in zip(x_list,y_list)]}]}
                elif chart["type"] == "Scatter":
                    options = {"xAxis":{"type":"category","data":x_list}, "yAxis":{"type":"value"}, "series":[{"data":[[x_list[i], y_list[i]] for i in range(len(x_list))],"type":"scatter"}]}
                elif chart["type"] == "Radar":
                    options = {"tooltip":{}, "radar":{"indicator":[{"name":str(n),"max":max(y_list)+5} for n in x_list]}, "series":[{"type":"radar","data":[{"value":y_list,"name":"Count"}]}]}
                elif chart["type"] == "Funnel":
                    options = {"tooltip":{"trigger":"item"}, "series":[{"type":"funnel","data":[{"value":v,"name":n} for n,v in zip(x_list,y_list)]}]}
                elif chart["type"] == "Gauge":
                    options = {"series":[{"type":"gauge","detail":{"formatter":"{value}"},"data":[{"value":sum(y_list),"name":"Total"}]}]}
                elif chart["type"] == "Treemap":
                    options = {"series":[{"type":"treemap","data":[{"name":str(n),"value":v} for n,v in zip(x_list,y_list)]}]}
                elif chart["type"] == "Word Cloud":
                    options = {"series":[{"type":"wordCloud","data":[{"name":str(n),"value":v} for n,v in zip(x_list,y_list)]}]}

                st_echarts(options=options, height=chart["height"])
