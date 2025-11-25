import streamlit as st
import pandas as pd
import os
from PIL import Image
import plotly.express as px

EXCEL_PATH = "uat_issues.xlsx"

# ----------------------------------------------------------
# CLIENT COLUMNS (EXACT AS PROVIDED)
# ----------------------------------------------------------
CLIENT_COLUMNS = [
    "Portfolio Demo",
    "Diabetes",
    "TMW",
    "MDR",
    "EDL",
    "STF",
    "IPRG Demo"
]


# ----------------------------------------------------------
# LOAD EXCEL
# ----------------------------------------------------------
@st.cache_data(ttl=5)
def load_excel():
    xls = pd.ExcelFile(EXCEL_PATH)
    sheet_names = [s.lower() for s in xls.sheet_names]

    if "uat_issues" in sheet_names:
        df_main = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("uat_issues")])
    else:
        df_main = pd.DataFrame()  # empty fallback

    if "architecture_issues" in sheet_names:
        df_arch = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("architecture_issues")])
    else:
        df_arch = pd.DataFrame()  # empty fallback

    # Strip spaces from headers
    df_main.columns = df_main.columns.str.strip()
    df_arch.columns = df_arch.columns.str.strip()

    return df_main, df_arch


# ----------------------------------------------------------
# SAVE EXCEL
# ----------------------------------------------------------
def save_excel(df_main, df_arch):
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="uat_issues", index=False)
        df_arch.to_excel(writer, sheet_name="architecture_issues", index=False)


# ----------------------------------------------------------
# APP CONFIG
# ----------------------------------------------------------
st.set_page_config(page_title="UAT Bug Tracker", layout="wide")
st.title("🧪 UAT Bug & Issue Tracker")

page = st.sidebar.radio(
    "Navigation",
    ("📊 Dashboard", "📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)")
)

# Load data
df_main, df_arch = load_excel()

# Only include client columns that exist
client_cols = [c for c in CLIENT_COLUMNS if c in df_main.columns]


# ============================================================
# PAGE 1 — DASHBOARD
# ============================================================
if page == "📊 Dashboard":

    st.header("Dashboard Overview")

    # Filters
    type_filter = st.multiselect("Filter by Type", df_main["Type"].unique())
    client_filter = st.multiselect("Filter by Client Resolved (Yes)", client_cols)

    filtered_df = df_main.copy()

    if type_filter:
        filtered_df = filtered_df[filtered_df["Type"].isin(type_filter)]

    if client_filter:
        filtered_df = filtered_df[filtered_df[client_filter].eq("Yes").all(axis=1)]

    # --- Charts ---
    col1, col2 = st.columns(2)

    with col1:
        if "Type" in filtered_df.columns:
            fig1 = px.histogram(filtered_df, x="Type", title="Count by Issue Type")
            st.plotly_chart(fig1, use_container_width=True)

    with col2:
        if client_cols:
            counts = filtered_df[client_cols].apply(lambda x: (x == "Yes").sum())
            fig2 = px.bar(counts, title="Resolved Count Per Client")
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Filtered Data")
    st.dataframe(filtered_df, use_container_width=True)

    # ---- Image Preview ----
    st.subheader("Preview Issue Image by SNo")

    if "Sno." in df_main.columns:
        sno = st.number_input("Enter Sno.", min_value=1, step=1)

        img_row = df_main[df_main["Sno."] == sno]
        if not img_row.empty:
            img_path = img_row["image"].iloc[0]
            if isinstance(img_path, str) and os.path.exists(img_path):
                try:
                    img = Image.open(img_path)
                    st.image(img, width=600)
                except:
                    st.error("Could not display the image.")
            else:
                st.warning("No valid image path found.")


# ============================================================
# PAGE 2 — EDIT UAT ISSUES
# ============================================================
elif page == "📋 UAT Issues (Editable)":

    st.header("Edit UAT Issues Sheet")

    edited_main = st.experimental_data_editor(
        df_main,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Save UAT Sheet"):
        save_excel(edited_main, df_arch)
        st.success("UAT Issues successfully saved.")

    st.download_button(
        "⬇ Download Updated Excel",
        data=open(EXCEL_PATH, "rb").read(),
        file_name="uat_issues_updated.xlsx"
    )


# ============================================================
# PAGE 3 — EDIT ARCHITECTURE ISSUES
# ============================================================
elif page == "🏗️ Architecture Issues (Editable)":

    st.header("Edit Architecture Issues Sheet")

    edited_arch = st.experimental_data_editor(
        df_arch,
        num_rows="dynamic",
        use_container_width=True
    )

    if st.button("💾 Save Architecture Sheet"):
        save_excel(df_main, edited_arch)
        st.success("Architecture Issues saved.")

    st.download_button(
        "⬇ Download Updated Excel",
        data=open(EXCEL_PATH, "rb").read(),
        file_name="architecture_issues_updated.xlsx"
    )
