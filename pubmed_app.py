import streamlit as st
import pandas as pd
import os
from io import BytesIO
import plotly.express as px
from datetime import datetime

# ------------------------ CONFIG ------------------------
EXCEL_PATH = "uat_issues.xlsx"
FEEDBACK_PATH = "user_feedback.xlsx"
MEDIA_FOLDER = "media"
CLIENT_COLUMNS = ["Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo"]

st.set_page_config(page_title="Bug Tracker Dashboard", layout="wide")
st.title("🧪 Bug Tracker Dashboard with Media & Feedback")

os.makedirs(MEDIA_FOLDER, exist_ok=True)

# ------------------------ LOAD EXCEL ------------------------
@st.cache_data(ttl=5)
def load_excel():
    # UAT Issues
    if os.path.exists(EXCEL_PATH):
        xls = pd.ExcelFile(EXCEL_PATH)
        sheet_names = [s.lower() for s in xls.sheet_names]

        if "uat_issues" in sheet_names:
            df_main = pd.read_excel(EXCEL_PATH, sheet_name="uat_issues")
        else:
            df_main = pd.DataFrame(columns=["Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue", *CLIENT_COLUMNS, "image", "video", "remarks", "dev status"])

        if "architecture_issues" in sheet_names:
            df_arch = pd.read_excel(EXCEL_PATH, sheet_name="architecture_issues")
        else:
            df_arch = pd.DataFrame(columns=["Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue", "Status", "image", "video", "remarks", "dev status"])
    else:
        df_main = pd.DataFrame(columns=["Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue", *CLIENT_COLUMNS, "image", "video", "remarks", "dev status"])
        df_arch = pd.DataFrame(columns=["Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue", "Status", "image", "video", "remarks", "dev status"])
    
    # Feedback sheet
    if os.path.exists(FEEDBACK_PATH):
        df_feedback = pd.read_excel(FEEDBACK_PATH)
    else:
        df_feedback = pd.DataFrame(columns=["Date", "User", "Feedback"])
    
    return df_main, df_arch, df_feedback

df_main, df_arch, df_feedback = load_excel()

# ------------------------ SAVE EXCEL ------------------------
def save_excel(df_main, df_arch):
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="uat_issues", index=False)
        df_arch.to_excel(writer, sheet_name="architecture_issues", index=False)

def save_feedback(df_feedback):
    df_feedback.to_excel(FEEDBACK_PATH, index=False)

# ------------------------ SIDEBAR ------------------------
page = st.sidebar.radio("Select Page", ["📊 Dashboard", "📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)", "📝 User Feedback"])

# ------------------------ DASHBOARD ------------------------
if page == "📊 Dashboard":
    dashboard_type = st.radio("Choose Dashboard", ["UAT Issues", "Architecture Issues"])
    
    if dashboard_type == "UAT Issues":
        df = df_main.copy()
    else:
        df = df_arch.copy()

    st.header(f"📊 {dashboard_type} Dashboard")

    # Filters
    if "Type" in df.columns:
        selected_types = st.multiselect("Filter by Type", df["Type"].dropna().unique(), default=df["Type"].dropna().unique())
        if selected_types:
            df = df[df["Type"].isin(selected_types)]
    if dashboard_type == "UAT Issues":
        selected_clients = st.multiselect("Filter by Resolved Clients", [c for c in CLIENT_COLUMNS if c in df.columns], default=[c for c in CLIENT_COLUMNS if c in df.columns])
        if selected_clients:
            df = df[df[selected_clients].eq("Yes").all(axis=1)]
    elif dashboard_type == "Architecture Issues":
        if "Status" in df.columns:
            selected_status = st.multiselect("Filter by Status", df["Status"].dropna().unique(), default=df["Status"].dropna().unique())
            if selected_status:
                df = df[df["Status"].isin(selected_status)]

    # Column filter
    columns_to_show = st.multiselect("Select columns to display", df.columns.tolist(), default=df.columns.tolist())
    st.dataframe(df[columns_to_show], use_container_width=True)

    # Media preview in separate expandable section
    with st.expander("📂 Media Preview (Click to Expand)"):
        for idx, row in df.iterrows():
            st.markdown(f"**S.No {row.get('Sno.', idx+1)} | Issue: {row.get('Issue', '')}**")
            if "image" in row and pd.notna(row["image"]):
                for img in str(row["image"]).split("|"):
                    img = img.strip()
                    img_path = os.path.join(MEDIA_FOLDER, img)
                    if os.path.exists(img_path):
                        st.image(img_path, caption=img, use_column_width=True)
            if "video" in row and pd.notna(row["video"]):
                for vid in str(row["video"]).split("|"):
                    vid = vid.strip()
                    vid_path = os.path.join(MEDIA_FOLDER, vid)
                    if os.path.exists(vid_path):
                        st.video(vid_path)

    # Predefined Charts
    st.subheader("📊 Predefined Charts")
    if "Type" in df.columns and not df.empty:
        type_counts = df['Type'].value_counts().reset_index()
        type_counts.columns = ['Type', 'Count']
        fig_type = px.bar(type_counts, x='Type', y='Count', title='Issues by Type')
        st.plotly_chart(fig_type, use_container_width=True)
    if dashboard_type == "Architecture Issues" and "Status" in df.columns:
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status', 'Count']
        fig_status = px.pie(status_counts, names='Status', values='Count', title='Issues by Status')
        st.plotly_chart(fig_status, use_container_width=True)

    # Custom Chart
    st.subheader("📊 Custom Chart")
    chart_col = st.selectbox("Select column for custom chart", df.columns.tolist(), key=f"custom_{dashboard_type}")
    chart_type = st.selectbox("Select chart type", ["Bar", "Pie", "Histogram"], key=f"chart_type_{dashboard_type}")
    if chart_col:
        try:
            if chart_type == "Bar":
                fig = px.bar(df, x=chart_col, title=f"Bar Chart: {chart_col}")
            elif chart_type == "Pie":
                fig = px.pie(df, names=chart_col, title=f"Pie Chart: {chart_col}")
            elif chart_type == "Histogram":
                fig = px.histogram(df, x=chart_col, title=f"Histogram: {chart_col}")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Cannot generate chart: {e}")

# ------------------------ EDITABLE SHEETS ------------------------
elif page == "📋 UAT Issues (Editable)":
    st.header("📋 Edit UAT Issues")

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("💾 Save Sheet (Sticky)"):
            save_excel(df_main, df_arch)
            st.success("UAT Issues saved.")
    with col2:
        st.download_button("⬇ Download Excel", data=open(EXCEL_PATH,"rb").read(), file_name="uat_issues_updated.xlsx")

    edited_main = st.experimental_data_editor(df_main, num_rows="dynamic", use_container_width=True)

    # Upload media per row
    for idx in edited_main.index:
        st.markdown(f"**Row {idx+1}: {edited_main.at[idx,'Issue'] if 'Issue' in edited_main.columns else ''}**")
        img_file = st.file_uploader(f"Upload Image for row {idx+1}", type=["png","jpg","jpeg"], key=f"img_{idx}")
        vid_file = st.file_uploader(f"Upload Video for row {idx+1}", type=["mp4","mov"], key=f"vid_{idx}")
        if img_file:
            path = os.path.join(MEDIA_FOLDER, img_file.name)
            with open(path,"wb") as f:
                f.write(img_file.getbuffer())
            if pd.notna(edited_main.at[idx,"image"]):
                edited_main.at[idx,"image"] += f"|{img_file.name}"
            else:
                edited_main.at[idx,"image"] = img_file.name
        if vid_file:
            path = os.path.join(MEDIA_FOLDER, vid_file.name)
            with open(path,"wb") as f:
                f.write(vid_file.getbuffer())
            if pd.notna(edited_main.at[idx,"video"]):
                edited_main.at[idx,"video"] += f"|{vid_file.name}"
            else:
                edited_main.at[idx,"video"] = vid_file.name

    df_main = edited_main.copy()

elif page == "🏗️ Architecture Issues (Editable)":
    st.header("🏗️ Edit Architecture Issues")

    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("💾 Save Sheet (Sticky)"):
            save_excel(df_main, df_arch)
            st.success("Architecture Issues saved.")
    with col2:
        st.download_button("⬇ Download Excel", data=open(EXCEL_PATH,"rb").read(), file_name="architecture_issues_updated.xlsx")

    edited_arch = st.experimental_data_editor(df_arch, num_rows="dynamic", use_container_width=True)

    # Upload media per row
    for idx in edited_arch.index:
        st.markdown(f"**Row {idx+1}: {edited_arch.at[idx,'Issue'] if 'Issue' in edited_arch.columns else ''}**")
        img_file = st.file_uploader(f"Upload Image for row {idx+1}", type=["png","jpg","jpeg"], key=f"arch_img_{idx}")
        vid_file = st.file_uploader(f"Upload Video for row {idx+1}", type=["mp4","mov"], key=f"arch_vid_{idx}")
        if img_file:
            path = os.path.join(MEDIA_FOLDER, img_file.name)
            with open(path,"wb") as f:
                f.write(img_file.getbuffer())
            if pd.notna(edited_arch.at[idx,"image"]):
                edited_arch.at[idx,"image"] += f"|{img_file.name}"
            else:
                edited_arch.at[idx,"image"] = img_file.name
        if vid_file:
            path = os.path.join(MEDIA_FOLDER, vid_file.name)
            with open(path,"wb") as f:
                f.write(vid_file.getbuffer())
            if pd.notna(edited_arch.at[idx,"video"]):
                edited_arch.at[idx,"video"] += f"|{vid_file.name}"
            else:
                edited_arch.at[idx,"video"] = vid_file.name

    df_arch = edited_arch.copy()

# ------------------------ USER FEEDBACK ------------------------
elif page == "📝 User Feedback":
    st.header("📝 User Feedback")
    with st.form("feedback_form", clear_on_submit=True):
        name = st.text_input("Your Name")
        feedback = st.text_area("Your Feedback")
        submitted = st.form_submit_button("Submit Feedback")
        if submitted:
            df_feedback = pd.concat([df_feedback, pd.DataFrame([{
                "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "User": name,
                "Feedback": feedback
            }])], ignore_index=True)
            save_feedback(df_feedback)
            st.success("Feedback submitted!")

    st.subheader("All Feedbacks")
    st.dataframe(df_feedback, use_container_width=True)
