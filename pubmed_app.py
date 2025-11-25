import streamlit as st
import pandas as pd
import os
from io import BytesIO
import plotly.express as px

EXCEL_PATH = "uat_issues.xlsx"
CLIENT_COLUMNS = ["Portfolio Demo","Diabetes","TMW","MDR","EDL","STF","IPRG Demo"]

# ------------------------ LOAD EXCEL ------------------------
@st.cache_data(ttl=5)
def load_excel():
    if not os.path.exists(EXCEL_PATH):
        st.error(f"Excel file {EXCEL_PATH} not found.")
        return pd.DataFrame(), pd.DataFrame()

    xls = pd.ExcelFile(EXCEL_PATH)
    sheet_names = [s.lower() for s in xls.sheet_names]

    # Load UAT Issues
    if "uat_issues" in sheet_names:
        df_main = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("uat_issues")])
    else:
        df_main = pd.DataFrame(columns=[
            "Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
            "Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo",
            "image", "remarks", "dev status", "video"
        ])

    # Load Architecture Issues
    if "architecture_issues" in sheet_names:
        df_arch = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("architecture_issues")])
    else:
        df_arch = pd.DataFrame(columns=[
            "Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
            "Status", "image", "remarks", "dev status", "video"
        ])

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
st.title("🧪 Bug Tracker Dashboard with Media Uploads & Charts")

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

        # Column filter
        columns_to_show = st.multiselect("Select columns to display", df_filtered.columns.tolist(), default=df_filtered.columns.tolist())
        st.dataframe(df_filtered[columns_to_show], use_container_width=True)

        # ------------------------ MEDIA VIEWER ------------------------
        st.subheader("🎬 Media Viewer")
        for idx, row in df_filtered.iterrows():
            with st.expander(f"Row {row.get('Sno.', '')}: {row.get('Issue', '')}"):
                # Images
                if "image" in row and pd.notna(row["image"]):
                    for img in str(row["image"]).split("|"):
                        st.image(img.strip(), caption="Screenshot", use_column_width=True)
                # Videos
                if "video" in row and pd.notna(row["video"]):
                    for vid in str(row["video"]).split("|"):
                        st.video(vid.strip())

        # ------------------------ PREDEFINED CHARTS ------------------------
        st.subheader("✅ Predefined Charts")
        if "Type" in df_filtered.columns:
            fig_type = px.bar(df_filtered['Type'].value_counts().reset_index(), x='index', y='Type',
                              labels={'index': 'Type', 'Type':'Count'}, title='Issues by Type')
            st.plotly_chart(fig_type, use_container_width=True)

        if selected_clients:
            client_counts = df_filtered[selected_clients].apply(lambda x: x=='Yes').sum()
            fig_client = px.bar(client_counts.reset_index(), x='index', y=selected_clients,
                                labels={'index':'Client','value':'Resolved Count'},
                                title="Issues Resolved per Client")
            st.plotly_chart(fig_client, use_container_width=True)

        if "dev status" in df_filtered.columns:
            dev_counts = df_filtered["dev status"].value_counts()
            fig_dev = px.pie(names=dev_counts.index, values=dev_counts.values, title="Dev Status Distribution")
            st.plotly_chart(fig_dev, use_container_width=True)

        # ------------------------ CUSTOM CHARTS ------------------------
        st.subheader("📊 Custom Charts")
        chart_x = st.selectbox("X-axis", df_filtered.columns, index=1)
        chart_y = st.selectbox("Y-axis", df_filtered.columns, index=2)
        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie"])

        if chart_type=="Bar":
            fig_custom = px.bar(df_filtered, x=chart_x, y=chart_y)
        elif chart_type=="Line":
            fig_custom = px.line(df_filtered, x=chart_x, y=chart_y)
        elif chart_type=="Scatter":
            fig_custom = px.scatter(df_filtered, x=chart_x, y=chart_y)
        elif chart_type=="Pie":
            fig_custom = px.pie(df_filtered, names=chart_x, values=chart_y)
        st.plotly_chart(fig_custom, use_container_width=True)

    else:  # Architecture Dashboard
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

        # Media Viewer
        st.subheader("🎬 Media Viewer")
        for idx, row in df_filtered.iterrows():
            with st.expander(f"Row {row.get('Sno.', '')}: {row.get('Issue', '')}"):
                if "image" in row and pd.notna(row["image"]):
                    for img in str(row["image"]).split("|"):
                        st.image(img.strip(), caption="Screenshot", use_column_width=True)
                if "video" in row and pd.notna(row["video"]):
                    for vid in str(row["video"]).split("|"):
                        st.video(vid.strip())

        # Predefined Charts
        st.subheader("✅ Predefined Charts")
        if "Type" in df_filtered.columns:
            fig_type = px.bar(df_filtered['Type'].value_counts().reset_index(), x='index', y='Type',
                              labels={'index': 'Type', 'Type':'Count'}, title='Issues by Type')
            st.plotly_chart(fig_type, use_container_width=True)

        if "Status" in df_filtered.columns:
            status_counts = df_filtered['Status'].value_counts()
            fig_status = px.pie(names=status_counts.index, values=status_counts.values, title="Status Distribution")
            st.plotly_chart(fig_status, use_container_width=True)

        # Custom Charts
        st.subheader("📊 Custom Charts")
        chart_x = st.selectbox("X-axis", df_filtered.columns, index=1, key="arch_x")
        chart_y = st.selectbox("Y-axis", df_filtered.columns, index=2, key="arch_y")
        chart_type = st.selectbox("Chart Type", ["Bar", "Line", "Scatter", "Pie"], key="arch_chart_type")

        if chart_type=="Bar":
            fig_custom = px.bar(df_filtered, x=chart_x, y=chart_y)
        elif chart_type=="Line":
            fig_custom = px.line(df_filtered, x=chart_x, y=chart_y)
        elif chart_type=="Scatter":
            fig_custom = px.scatter(df_filtered, x=chart_x, y=chart_y)
        elif chart_type=="Pie":
            fig_custom = px.pie(df_filtered, names=chart_x, values=chart_y)
        st.plotly_chart(fig_custom, use_container_width=True)

# ------------------------ EDITABLE TABLES ------------------------
elif page == "📋 UAT Issues (Editable)":
    st.header("📋 Edit UAT Issues")
    
    edited_main = st.experimental_data_editor(df_main, num_rows="dynamic", use_container_width=True)

    st.subheader("Upload Media for Last Row")
    uploaded_img = st.file_uploader("Upload Image", type=["png","jpg","jpeg"], key="uat_img")
    uploaded_vid = st.file_uploader("Upload Video", type=["mp4","mov"], key="uat_vid")

    if uploaded_img:
        edited_main.at[edited_main.index[-1], "image"] = uploaded_img.name
    if uploaded_vid:
        edited_main.at[edited_main.index[-1], "video"] = uploaded_vid.name

    if st.button("💾 Save UAT Sheet"):
        save_excel(edited_main, df_arch)
        st.success("UAT Issues saved.")

    st.download_button("⬇ Download Excel", data=open(EXCEL_PATH, "rb").read(), file_name="uat_issues_updated.xlsx")

elif page == "🏗️ Architecture Issues (Editable)":
    st.header("🏗️ Edit Architecture Issues")
    
    edited_arch = st.experimental_data_editor(df_arch, num_rows="dynamic", use_container_width=True)

    st.subheader("Upload Media for Last Row")
    uploaded_img = st.file_uploader("Upload Image", type=["png","jpg","jpeg"], key="arch_img")
    uploaded_vid = st.file_uploader("Upload Video", type=["mp4","mov"], key="arch_vid")

    if uploaded_img:
        edited_arch.at[edited_arch.index[-1], "image"] = uploaded_img.name
    if uploaded_vid:
        edited_arch.at[edited_arch.index[-1], "video"] = uploaded_vid.name

    if st.button("💾 Save Architecture Sheet"):
        save_excel(df_main, edited_arch)
        st.success("Architecture Issues saved.")

    st.download_button("⬇ Download Excel", data=open(EXCEL_PATH, "rb").read(), file_name="architecture_issues_updated.xlsx")
