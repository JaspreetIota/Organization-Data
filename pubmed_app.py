import streamlit as st
import pandas as pd
import os
from PIL import Image
import plotly.express as px

EXCEL_PATH = "uat_issues.xlsx"

# ----------------------------------------------------------
# CLIENT STATUS COLUMNS (your exact column names)
# ----------------------------------------------------------
CLIENT_COLUMNS = [
    "⭐Portfolio Demo",
    "⭐Diabetes",
    "⭐TMW",
    "MDR",
    "EDL",
    "STF",
    "IPRG Demo"
]


# ----------------------------------------------------------
# LOAD EXCEL (AUTO-DETECT SHEET NAMES)
# ----------------------------------------------------------
@st.cache_data(ttl=5)
def load_excel():
    """Load Excel safely and return both sheets."""
    xls = pd.ExcelFile(EXCEL_PATH)

    # Try exact names, fallback to first two sheets
    sheet_names = xls.sheet_names

    # MAIN SHEET
    if "uat_issues" in sheet_names:
        df_main = pd.read_excel(EXCEL_PATH, sheet_name="uat_issues")
    else:
        df_main = pd.read_excel(EXCEL_PATH, sheet_name=sheet_names[0])

    # ARCHITECTURE SHEET
    if "architecture_issues" in sheet_names:
        df_arch = pd.read_excel(EXCEL_PATH, sheet_name="architecture_issues")
    else:
        df_arch = pd.read_excel(EXCEL_PATH, sheet_name=sheet_names[1])

    return df_main, df_arch


# ----------------------------------------------------------
# SAVE FUNCTION
# ----------------------------------------------------------
def save_excel(df_main, df_arch):
    with pd.ExcelWriter(EXCEL_PATH, engine='openpyxl') as writer:
        df_main.to_excel(writer, sheet_name="uat_issues", index=False)
        df_arch.to_excel(writer, sheet_name="architecture_issues", index=False)


# ----------------------------------------------------------
# BASIC PAGE CONFIG
# ----------------------------------------------------------
st.set_page_config(page_title="UAT Bug Tracker", layout="wide")
st.title("🧪 UAT Bug & Issue Tracker")

page = st.sidebar.radio(
    "Navigation",
    ["📊 Dashboard", "📋 Editable Table – Main Issues", "🏗️ Architecture Issues"]
)


# ----------------------------------------------------------
# LOAD DATA
# ----------------------------------------------------------
df_main, df_arch = load_excel()

# Ensure client columns exist
client_cols = [c for c in CLIENT_COLUMNS if c in df_main.columns]


# ==========================================================
# PAGE 1 — DASHBOARD
# ==========================================================
if page == "📊 Dashboard":

    st.header("Interactive Dashboard")

    # ---------------- FILTERS ----------------
    type_filter = st.multiselect("Filter by Type", df_main["Type"].unique())
    client_filter = st.multiselect("Filter by Client (Resolved: Yes)", client_cols)

    filtered_df = df_main.copy()

    if type_filter:
        filtered_df = filtered_df[filtered_df["Type"].isin(type_filter)]

    if client_filter:
        filtered_df = filtered_df[filtered_df[client_filter].eq("Yes").all(axis=1)]

    # ---------------- CHARTS ----------------
    col1, col2 = st.columns(2)

    with col1:
        if "Type" in filtered_df.columns:
            fig1 = px.histogram(filtered_df, x="Type", title="Issues by Type")
            st.plotly_chart(fig1, use_container_width=True)

    with col2:
        if client_cols:
            mdf = filtered_df[client_cols].apply(lambda x: (x == "Yes").sum())
            fig2 = px.bar(mdf, title="Client-Wise Resolved Count")
            st.plotly_chart(fig2, use_container_width=True)

    # ---------------- TABLE ----------------
    st.subheader("Filtered Issue List")
    st.dataframe(filtered_df, use_container_width=True)

    # ---------------- IMAGE PREVIEW ----------------
    st.subheader("Image Preview by SNo")

    if "SNo" in df_main.columns:
        issue_id = st.number_input("Enter SNo:", min_value=1, step=1)

        img_row = df_main[df_main["SNo"] == issue_id]
        if not img_row.empty:
            img_path = img_row["Image"].iloc[0]
            if isinstance(img_path, str) and os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    st.image(img, width=600)
                except:
                    st.error("Cannot open the image file.")
            else:
                st.warning("Image path not valid.")


# ==========================================================
# PAGE 2 — EDIT MAIN ISSUES
# ==========================================================
elif page == "📋 Editable Table – Main Issues":

    st.header("Edit Main UAT Issues")

    edited_df = st.experimental_data_editor(
        df_main,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Save Changes"):
        save_excel(edited_df, df_arch)
        st.success("Main UAT Issues Sheet Updated.")

    st.download_button(
        "⬇ Download Excel File",
        data=open(EXCEL_PATH, "rb").read(),
        file_name="UAT_Issues_Updated.xlsx"
    )


# ==========================================================
# PAGE 3 — EDIT ARCHITECTURE ISSUES
# ==========================================================
elif page == "🏗️ Architecture Issues":

    st.header("Architecture Specific Issues")

    edited_arch = st.experimental_data_editor(
        df_arch,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Save Architecture Changes"):
        save_excel(df_main, edited_arch)
        st.success("Architecture Sheet Updated.")

    st.download_button(
        "⬇ Download Updated Excel",
        data=open(EXCEL_PATH, "rb").read(),
        file_name="Architecture_Issues_Updated.xlsx"
    )
