import streamlit as st
import pandas as pd
import numpy as np
from streamlit_echarts import st_echarts
import json
import os

st.title("Custom Dashboard Builder")

# --- Upload dataset ---
uploaded = st.file_uploader("Upload Excel/CSV", type=["xlsx", "csv"])
if uploaded:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)

    df = df.replace([np.nan, np.inf, -np.inf], None)
    columns = df.columns.tolist()
    st.write("### Data Preview", df)

    # --- Dashboard state ---
    if "dashboard" not in st.session_state:
        st.session_state.dashboard = []

    # --- Add new chart ---
    with st.expander("Add New Chart"):
        x_axis = st.selectbox("X-axis", options=columns, key="new_x")
        y_axis = st.selectbox("Y-axis (numeric or <count>)", options=["<count>"] + columns, key="new_y")
        chart_type = st.selectbox(
            "Chart Type",
            ["Bar", "Stacked Bar", "Horizontal Bar", "Line", "Area", "Stacked Area",
             "Pie", "Donut", "Scatter", "Radar", "Funnel", "Gauge", "Treemap", "Word Cloud"],
            key="new_type"
        )
        width = st.slider("Width (columns)", 2, 12, 6, key="new_width")
        height = st.slider("Height (pixels)", 200, 800, 400, key="new_height")

        if st.button("Add Chart"):
            chart_id = f"chart{len(st.session_state.dashboard)+1}"
            st.session_state.dashboard.append({
                "id": chart_id,
                "x_axis": x_axis,
                "y_axis": y_axis,
                "type": chart_type,
                "width": width,
                "height": height
            })

    # --- Save/Load Dashboard ---
    save_name = st.text_input("Dashboard name to save/load", "")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Save Dashboard") and save_name:
            os.makedirs("dashboards", exist_ok=True)
            with open(f"dashboards/{save_name}.json", "w") as f:
                json.dump(st.session_state.dashboard, f)
            st.success(f"Dashboard '{save_name}' saved!")
    with col2:
        if st.button("Load Dashboard") and save_name:
            try:
                with open(f"dashboards/{save_name}.json") as f:
                    st.session_state.dashboard = json.load(f)
                st.success(f"Dashboard '{save_name}' loaded!")
            except:
                st.error("Dashboard not found.")

    st.write("---")
    st.subheader("Your Dashboard")

    # --- Render all charts ---
    for i, chart in enumerate(st.session_state.dashboard):
        cols = st.columns([chart["width"], 12 - chart["width"]])
        with cols[0]:
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

            # --- Build chart options ---
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
            # You can add Gauge, Treemap, Word Cloud options if needed

            st_echarts(options=options, height=chart["height"])
