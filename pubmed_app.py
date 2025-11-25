import streamlit as st
import pandas as pd
import os
from PIL import Image
import plotly.express as px

EXCEL_PATH = "uat_issues.xlsx"

# Client columns
CLIENT_COLUMNS = ["Portfolio Demo","Diabetes","TMW","MDR","EDL","STF","IPRG Demo"]

# ------------------------ LOAD EXCEL ------------------------
@st.cache_data(ttl=5)
def load_excel():
    if not os.path.exists(EXCEL_PATH):
        st.error(f"Excel file {EXCEL_PATH} not found.")
        return pd.DataFrame(), pd.DataFrame()

    xls = pd.ExcelFile(EXCEL_PATH)
    sheet_names = [s.lower() for s in xls.sheet_names]

    # Load UAT issues
    if "uat_issues" in sheet_names:
        df_main = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("uat_issues")])
    else:
        df_main = pd.DataFrame(columns=[
            "Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
            "Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo",
            "image", "Remarks", "Dev Status"
        ])

    # Load Architecture issues
    if "architecture_issues" in sheet_names:
        df_arch = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("architecture_issues")])
    else:
        df_arch = pd.DataFrame(columns=[
            "Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
            "Status", "image", "Remarks", "Dev Status"
        ])

    # Strip spaces from headers
    df_main.columns = df_main.columns.str.strip()
    df_arch.columns = df_arch.columns.str.strip()

    return df_main, df_arch

# ------------------------ SAVE EXCEL ------------------------
def save_excel(df_main, df_arch):
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="uat_issues", index=False)
        df_arch.to_excel(writer, sheet_name="architecture_issues", index=False)

# ------------------------ CONFIG ------------------------
st.set_page_config(page_title="UAT & Architecture Bug Tracker", layout="wide")
st.title("🧪 Bug Tracker Dashboard")

# Load data
df_main, df_arch = load_excel()

# ------------------------ SIDEBAR ------------------------
page = st.sidebar.radio("Select Page", ["📊 Dashboard", "📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)"])

# ------------------------ DASHBOARD ------------------------
if page == "📊 Dashboard":
    dashboard_type = st.radio("Choose Dashboard", ["UAT Issues", "Architecture Issues"])

    if dashboard_type == "UAT Issues":
        st.header("📊 UAT Issues Dashboard")

        # Filters
        type_options = df_main["Type"].unique().tolist() if "Type" in df_main.columns else []
        selected_types = st.multiselect("Filter by Type", type_options, default=type_options)

        client_options = [c for c in CLIENT_COLUMNS if c in df_main.columns]
        selected_clients = st.multiselect("Filter by Resolved Clients", client_options, default=client_options)

        df_filtered = df_main.copy()
        if selected_types:
            df_filtered = df_filtered[df_filtered["Type"].isin(selected_types)]
        if selected_clients:
            df_filtered = df_filtered[df_filtered[selected_clients].eq("Yes").all(axis=1)]

        # Column filter for table
        columns_to_show = st.multiselect("Select columns to display", df_filtered.columns.tolist(), default=df_filtered.columns.tolist())
        st.dataframe(df_filtered[columns_to_show], use_container_width=True)

        # Dynamic Charts
        st.subheader("Charts")
        chart_column = st.selectbox("Select column for chart", df_filtered.columns.tolist())
        chart_type = st.selectbox("Select chart type", ["Bar", "Histogram", "Pie"])

        if chart_column:
            if chart_type == "Bar":
                fig = px.bar(df_filtered, x=chart_column, title=f"Bar Chart: {chart_column}")
            elif chart_type == "Histogram":
                fig = px.histogram(df_filtered, x=chart_column, title=f"Histogram: {chart_column}")
            elif chart_type == "Pie":
                fig = px.pie(df_filtered, names=chart_column, title=f"Pie Chart: {chart_column}")
            st.plotly_chart(fig, use_container_width=True)

    else:
        st.header("🏗️ Architecture Issues Dashboard")
        type_options = df_arch["Type"].unique().tolist() if "Type" in df_arch.columns else []
        selected_types = st.multiselect("Filter by Type", type_options, default=type_options)
        status_options = df_arch["Status"].unique().tolist() if "Status" in df_arch.columns else []
        selected_status = st.multiselect("Filter by Status", status_options, default=status_options)

        df_filtered = df_arch.copy()
        if selected_types:
            df_filtered = df_filtered[df_filtered["Type"].isin(selected_types)]
        if selected_status:
            df_filtered = df_filtered[df_filtered["Status"].isin(selected_status)]

        # Column filter
        columns_to_show = st.multiselect("Select columns to display", df_filtered.columns.tolist(), default=df_filtered.columns.tolist())
        st.dataframe(df_filtered[columns_to_show], use_container_width=True)

        # Dynamic Charts
        st.subheader("Charts")
        chart_column = st.selectbox("Select column for chart", df_filtered.columns.tolist())
        chart_type = st.selectbox("Select chart type", ["Bar", "Histogram", "Pie"], key="arch_chart")
        if chart_column:
            if chart_type == "Bar":
                fig = px.bar(df_filtered, x=chart_column, title=f"Bar Chart: {chart_column}")
            elif chart_type == "Histogram":
                fig = px.histogram(df_filtered, x=chart_column, title=f"Histogram: {chart_column}")
            elif chart_type == "Pie":
                fig = px.pie(df_filtered, names=chart_column, title=f"Pie Chart: {chart_column}")
            st.plotly_chart(fig, use_container_width=True)

# ------------------------ EDITABLE TABLES ------------------------
elif page == "📋 UAT Issues (Editable)":
    st.header("📋 Edit UAT Issues")
    edited_main = st.experimental_data_editor(df_main, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Save UAT Sheet"):
        save_excel(edited_main, df_arch)
        st.success("UAT Issues saved.")
    st.download_button("⬇ Download Excel", data=open(EXCEL_PATH, "rb").read(), file_name="uat_issues_updated.xlsx")

elif page == "🏗️ Architecture Issues (Editable)":
    st.header("🏗️ Edit Architecture Issues")
    edited_arch = st.experimental_data_editor(df_arch, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Save Architecture Sheet"):
        save_excel(df_main, edited_arch)
        st.success("Architecture Issues saved.")
    st.download_button("⬇ Download Excel", data=open(EXCEL_PATH, "rb").read(), file_name="architecture_issues_updated.xlsx")
