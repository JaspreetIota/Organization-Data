import streamlit as st
import pandas as pd
import os
from io import BytesIO
import plotly.express as px

EXCEL_PATH = "uat_issues.xlsx"
MEDIA_FOLDER = "media"

CLIENT_COLUMNS = ["Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo"]

# ------------------------ LOAD EXCEL ------------------------
@st.cache_data(ttl=5)
def load_excel():
    if not os.path.exists(EXCEL_PATH):
        st.error(f"Excel file {EXCEL_PATH} not found.")
        return pd.DataFrame(), pd.DataFrame()

    xls = pd.ExcelFile(EXCEL_PATH)
    sheet_names = [s.lower() for s in xls.sheet_names]

    if "uat_issues" in sheet_names:
        df_main = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("uat_issues")])
    else:
        df_main = pd.DataFrame(columns=[
            "Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
            *CLIENT_COLUMNS, "image", "video", "remarks", "dev status"
        ])

    if "architecture_issues" in sheet_names:
        df_arch = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("architecture_issues")])
    else:
        df_arch = pd.DataFrame(columns=[
            "Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
            "Status", "image", "video", "remarks", "dev status"
        ])

    # Normalize column names: lowercase and strip whitespace
    df_main.columns = df_main.columns.str.strip().str.lower()
    df_arch.columns = df_arch.columns.str.strip().str.lower()

    return df_main, df_arch

# ------------------------ SAVE EXCEL ------------------------
def save_excel(df_main, df_arch):
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="uat_issues", index=False)
        df_arch.to_excel(writer, sheet_name="architecture_issues", index=False)

# ------------------------ CONFIG ------------------------
st.set_page_config(page_title="UAT & Architecture Bug Tracker", layout="wide")
st.title("🧪 Bug Tracker Dashboard with Media Uploads & Custom Charts")

# Ensure media folder exists
os.makedirs(MEDIA_FOLDER, exist_ok=True)

# Load data
df_main, df_arch = load_excel()

# ------------------------ SIDEBAR ------------------------
page = st.sidebar.radio("Select Page", ["📊 Dashboard", "📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)"])

# --- CSS for sticky buttons at top ---
st.markdown("""
<style>
.sticky-container {
    position: sticky;
    top: 0;
    background-color: white;
    padding: 10px 0;
    z-index: 100;
    border-bottom: 1px solid #ddd;
}
</style>
""", unsafe_allow_html=True)

# ------------------------ DASHBOARD ------------------------
if page == "📊 Dashboard":
    dashboard_type = st.radio("Choose Dashboard", ["UAT Issues", "Architecture Issues"])

    if dashboard_type == "UAT Issues":
        st.header("📊 UAT Issues Dashboard")

        # Filters
        type_options = df_main["type"].dropna().unique().tolist() if "type" in df_main.columns else []
        selected_types = st.multiselect("Filter by Type", type_options, default=type_options)

        client_options = [c.lower() for c in CLIENT_COLUMNS if c.lower() in df_main.columns]
        selected_clients = st.multiselect("Filter by Resolved Clients", client_options, default=client_options)

        df_filtered = df_main.copy()
        if selected_types:
            df_filtered = df_filtered[df_filtered["type"].isin(selected_types)]
        if selected_clients:
            df_filtered = df_filtered[df_filtered[selected_clients].eq("Yes").all(axis=1)]

        # Column filter
        columns_to_show = st.multiselect("Select columns to display", df_filtered.columns.tolist(), default=df_filtered.columns.tolist())
        st.dataframe(df_filtered[columns_to_show], use_container_width=True)

        # Predefined Charts
        st.subheader("Predefined Charts")
        if "type" in df_filtered.columns and not df_filtered.empty:
            type_counts = df_filtered['type'].value_counts().reset_index()
            type_counts.columns = ['Type', 'Count']
            if not type_counts.empty:
                fig_type = px.bar(type_counts, x='Type', y='Count', title='Issues by Type')
                st.plotly_chart(fig_type, use_container_width=True)

        # Custom Charts
        st.subheader("Custom Chart")
        chart_col = st.selectbox("Select column for chart", df_filtered.columns.tolist(), key="uat_chart_col")
        chart_type = st.selectbox("Select chart type", ["Bar", "Pie", "Histogram"], key="uat_chart_type")
        if chart_col:
            try:
                if chart_type == "Bar":
                    fig = px.bar(df_filtered, x=chart_col, title=f"Bar Chart: {chart_col}")
                elif chart_type == "Pie":
                    fig = px.pie(df_filtered, names=chart_col, title=f"Pie Chart: {chart_col}")
                elif chart_type == "Histogram":
                    fig = px.histogram(df_filtered, x=chart_col, title=f"Histogram: {chart_col}")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Cannot generate chart for column '{chart_col}': {e}")

        # Media preview in separate expandable section
        with st.expander("🖼️📹 Expand Media Preview Section"):
            if df_filtered.empty:
                st.info("No records to show media.")
            else:
                for idx, row in df_filtered.iterrows():
                    with st.expander(f"S.No: {row.get('sno.', '')} | Issue: {row.get('issue', '')}"):
                        if "image" in row and pd.notna(row["image"]):
                            for img in str(row["image"]).split("|"):
                                img = img.strip()
                                if img:
                                    img_path = os.path.join(MEDIA_FOLDER, img)
                                    if os.path.exists(img_path):
                                        st.image(img_path, caption=img, use_column_width=True)
                        if "video" in row and pd.notna(row["video"]):
                            for vid in str(row["video"]).split("|"):
                                vid = vid.strip()
                                if vid:
                                    vid_path = os.path.join(MEDIA_FOLDER, vid)
                                    if os.path.exists(vid_path):
                                        st.video(vid_path)

    else:  # Architecture Issues Dashboard
        st.header("🏗️ Architecture Issues Dashboard")
        type_options = df_arch["type"].dropna().unique().tolist() if "type" in df_arch.columns else []
        selected_types = st.multiselect("Filter by Type", type_options, default=type_options)
        status_options = df_arch["status"].dropna().unique().tolist() if "status" in df_arch.columns else []
        selected_status = st.multiselect("Filter by Status", status_options, default=status_options)

        df_filtered = df_arch.copy()
        if selected_types:
            df_filtered = df_filtered[df_filtered["type"].isin(selected_types)]
        if selected_status:
            df_filtered = df_filtered[df_filtered["status"].isin(selected_status)]

        columns_to_show = st.multiselect("Select columns to display", df_filtered.columns.tolist(), default=df_filtered.columns.tolist())
        st.dataframe(df_filtered[columns_to_show], use_container_width=True)

        # Predefined Charts
        st.subheader("Predefined Charts")
        if "type" in df_filtered.columns and not df_filtered.empty:
            type_counts = df_filtered['type'].value_counts().reset_index()
            type_counts.columns = ['Type', 'Count']
            if not type_counts.empty:
                fig_type = px.bar(type_counts, x='Type', y='Count', title='Architecture Issues by Type')
                st.plotly_chart(fig_type, use_container_width=True)
        if "status" in df_filtered.columns and not df_filtered.empty:
            status_counts = df_filtered['status'].value_counts().reset_index()
            status_counts.columns = ['Status', 'Count']
            if not status_counts.empty:
                fig_status = px.pie(status_counts, names='Status', values='Count', title='Architecture Issues Status')
                st.plotly_chart(fig_status, use_container_width=True)

        # Custom Charts
        st.subheader("Custom Chart")
        chart_col = st.selectbox("Select column for chart", df_filtered.columns.tolist(), key="arch_chart_col")
        chart_type = st.selectbox("Select chart type", ["Bar", "Pie", "Histogram"], key="arch_chart_type")
        if chart_col:
            try:
                if chart_type == "Bar":
                    fig = px.bar(df_filtered, x=chart_col, title=f"Bar Chart: {chart_col}")
                elif chart_type == "Pie":
                    fig = px.pie(df_filtered, names=chart_col, title=f"Pie Chart: {chart_col}")
                elif chart_type == "Histogram":
                    fig = px.histogram(df_filtered, x=chart_col, title=f"Histogram: {chart_col}")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Cannot generate chart for column '{chart_col}': {e}")

        # Media preview in separate expandable section
        with st.expander("🖼️📹 Expand Media Preview Section"):
            if df_filtered.empty:
                st.info("No records to show media.")
            else:
                for idx, row in df_filtered.iterrows():
                    with st.expander(f"S.No: {row.get('sno.', '')} | Issue: {row.get('issue', '')}"):
                        if "image" in row and pd.notna(row["image"]):
                            for img in str(row["image"]).split("|"):
                                img = img.strip()
                                if img:
                                    img_path = os.path.join(MEDIA_FOLDER, img)
                                    if os.path.exists(img_path):
                                        st.image(img_path, caption=img, use_column_width=True)
                        if "video" in row and pd.notna(row["video"]):
                            for vid in str(row["video"]).split("|"):
                                vid = vid.strip()
                                if vid:
                                    vid_path = os.path.join(MEDIA_FOLDER, vid)
                                    if os.path.exists(vid_path):
                                        st.video(vid_path)

# ------------------------ EDITABLE SHEETS ------------------------
elif page == "📋 UAT Issues (Editable)":
    st.header("📋 Edit UAT Issues")

    # Sticky save/download container at top
    with st.container():
        st.markdown('<div class="sticky-container">', unsafe_allow_html=True)
        edited_main = st.experimental_data_editor(df_main, num_rows="dynamic", use_container_width=True)
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("💾 Save UAT Sheet"):
                save_excel(edited_main, df_arch)
                st.success("UAT Issues saved.")
        with col2:
            st.download_button("⬇ Download Excel", data=open(EXCEL_PATH, "rb").read(), file_name="uat_issues_updated.xlsx")
        st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("Upload Media for Rows")
    for idx in edited_main.index:
        st.markdown(f"**Row {idx+1}: {edited_main.at[idx,'issue'] if 'issue' in edited_main.columns else ''}**")
        img_file = st.file_uploader(f"Upload Image for row {idx+1}", type=["png","jpg","jpeg"], key=f"img_{idx}")
        vid_file = st.file_uploader(f"Upload Video for row {idx+1}", type=["mp4","mov"], key=f"vid_{idx}")
        if img_file:
            path = os.path.join(MEDIA_FOLDER, img_file.name)
            with open(path, "wb") as f:
                f.write(img_file.getbuffer())
            edited_main.at[idx, "image"] = img_file.name
        if vid_file:
            path = os.path.join(MEDIA_FOLDER, vid_file.name)
            with open(path, "wb") as f:
                f.write(vid_file.getbuffer())
            edited_main.at[idx, "video"] = vid_file.name

elif page == "🏗️ Architecture Issues (Editable)":
    st.header("🏗️ Edit Architecture Issues")

    # Sticky save/download container at top
    with st.container():
        st.markdown('<div class="sticky-container">', unsafe_allow_html=True)
        edited_arch = st.experimental_data_editor(df_arch, num_rows="dynamic", use_container_width=True)
        col1, col2 = st.columns([1,1])
        with col1:
            if st.button("💾 Save Architecture Sheet"):
                save_excel(df_main, edited_arch)
                st.success("Architecture Issues saved.")
        with col2:
            st.download_button("⬇ Download Excel", data=open(EXCEL_PATH, "rb").read(), file_name="architecture_issues_updated.xlsx")
        st.markdown('</div>', unsafe_allow_html=True)

    st.subheader("Upload Media for Rows")
    for idx in edited_arch.index:
        st.markdown(f"**Row {idx+1}: {edited_arch.at[idx,'issue'] if 'issue' in edited_arch.columns else ''}**")
        img_file = st.file_uploader(f"Upload Image for row {idx+1}", type=["png","jpg","jpeg"], key=f"arch_img_{idx}")
        vid_file = st.file_uploader(f"Upload Video for row {idx+1}", type=["mp4","mov"], key=f"arch_vid_{idx}")
        if img_file:
            path = os.path.join(MEDIA_FOLDER, img_file.name)
            with open(path, "wb") as f:
                f.write(img_file.getbuffer())
            edited_arch.at[idx, "image"] = img_file.name
        if vid_file:
            path = os.path.join(MEDIA_FOLDER, vid_file.name)
            with open(path, "wb") as f:
                f.write(vid_file.getbuffer())
            edited_arch.at[idx, "video"] = vid_file.name
