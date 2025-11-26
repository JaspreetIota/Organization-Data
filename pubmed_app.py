import streamlit as st
import pandas as pd
import os
from io import BytesIO
import plotly.express as px

EXCEL_PATH = "uat_issues.xlsx"
MEDIA_FOLDER = "media"
FEEDBACK_FILE = "user_feedback.xlsx"

CLIENT_COLUMNS = ["Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo"]

# ------------------------ SETUP ------------------------
st.set_page_config(page_title="UAT & Architecture Bug Tracker", layout="wide")
os.makedirs(MEDIA_FOLDER, exist_ok=True)

# ------------------------ LOAD EXCEL ------------------------
@st.cache_data(ttl=5)
def load_excel():
    # UAT & Architecture Issues
    if not os.path.exists(EXCEL_PATH):
        df_main = pd.DataFrame(columns=[
            "Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
            *CLIENT_COLUMNS, "image", "video", "remarks", "dev status"
        ])
        df_arch = pd.DataFrame(columns=[
            "Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue",
            "Status", "image", "video", "remarks", "dev status"
        ])
    else:
        xls = pd.ExcelFile(EXCEL_PATH)
        sheet_names = [s.lower() for s in xls.sheet_names]

        df_main = pd.read_excel(EXCEL_PATH, sheet_name="uat_issues") if "uat_issues" in sheet_names else pd.DataFrame()
        df_arch = pd.read_excel(EXCEL_PATH, sheet_name="architecture_issues") if "architecture_issues" in sheet_names else pd.DataFrame()

    # Feedback sheet
    if os.path.exists(FEEDBACK_FILE):
        df_feedback = pd.read_excel(FEEDBACK_FILE)
    else:
        df_feedback = pd.DataFrame(columns=["Timestamp", "User", "Feedback", "image", "video"])

    # Ensure media columns exist
    for df in [df_main, df_arch, df_feedback]:
        for col in ["image", "video"]:
            if col not in df.columns:
                df[col] = ""

    return df_main, df_arch, df_feedback

# ------------------------ SAVE EXCEL ------------------------
def save_excel(df_main, df_arch):
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="uat_issues", index=False)
        df_arch.to_excel(writer, sheet_name="architecture_issues", index=False)

def save_feedback(df_feedback):
    df_feedback.to_excel(FEEDBACK_FILE, index=False)

# ------------------------ LOAD DATA ------------------------
df_main, df_arch, df_feedback = load_excel()

# ------------------------ SIDEBAR ------------------------
page = st.sidebar.radio("Select Page", ["📊 Dashboard", "📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)", "📝 User Feedback"])

# ------------------------ DASHBOARD ------------------------
if page == "📊 Dashboard":
    st.title("📊 Bug Tracker Dashboard")
    dashboard_type = st.radio("Select Dashboard", ["UAT Issues", "Architecture Issues"])

    df = df_main if dashboard_type == "UAT Issues" else df_arch

    if df.empty:
        st.warning("No data available for this sheet.")
    else:
        # Column selection
        columns_to_show = st.multiselect("Select Columns to Display", df.columns.tolist(), default=df.columns.tolist())
        st.dataframe(df[columns_to_show], use_container_width=True)

        # Expandable Media Viewer
        with st.expander("📁 Expandable Media Viewer"):
            for idx, row in df.iterrows():
                st.markdown(f"**S.No: {row.get('Sno.', '')} | Issue: {row.get('Issue', '')}**")
                # Images
                if pd.notna(row.get("image")) and row.get("image") != "":
                    for img in str(row["image"]).split("|"):
                        img = img.strip()
                        path = os.path.join(MEDIA_FOLDER, img)
                        if os.path.exists(path):
                            st.image(path, caption=img, use_column_width=True)
                # Videos
                if pd.notna(row.get("video")) and row.get("video") != "":
                    for vid in str(row["video"]).split("|"):
                        vid = vid.strip()
                        path = os.path.join(MEDIA_FOLDER, vid)
                        if os.path.exists(path):
                            st.video(path)

        # Predefined Charts
        st.subheader("Predefined Charts")
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

        # Custom Charts
        st.subheader("Custom Charts")
        chart_col = st.selectbox("Select column for chart", df.columns.tolist(), key=f"{dashboard_type}_chart_col")
        chart_type = st.selectbox("Select chart type", ["Bar", "Pie", "Histogram"], key=f"{dashboard_type}_chart_type")
        if chart_col:
            try:
                if chart_type == "Bar":
                    fig = px.bar(df, x=chart_col, title=f"{chart_type}: {chart_col}")
                elif chart_type == "Pie":
                    fig = px.pie(df, names=chart_col, title=f"{chart_type}: {chart_col}")
                elif chart_type == "Histogram":
                    fig = px.histogram(df, x=chart_col, title=f"{chart_type}: {chart_col}")
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Cannot generate chart for column '{chart_col}': {e}")

# ------------------------ EDITABLE SHEETS ------------------------
elif page == "📋 UAT Issues (Editable)":
    st.title("📋 Edit UAT Issues")
    st.markdown("💾 Save / Download options are sticky on top")

    # Save/Download buttons
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("💾 Save UAT Sheet"):
            save_excel(df_main, df_arch)
            st.success("UAT Issues saved.")
    with col2:
        st.download_button("⬇ Download Excel", data=open(EXCEL_PATH, "rb").read(), file_name="uat_issues_updated.xlsx")

    # Data editor
    edited_main = st.experimental_data_editor(df_main, num_rows="dynamic", use_container_width=True)
    df_main = edited_main.copy()

    # Media upload per row
    st.subheader("Upload Media for Rows")
    for idx in df_main.index:
        st.markdown(f"**Row {idx+1}: {df_main.at[idx,'Issue']}**")
        img_file = st.file_uploader(f"Upload Image for row {idx+1}", type=["png","jpg","jpeg"], key=f"img_{idx}")
        vid_file = st.file_uploader(f"Upload Video for row {idx+1}", type=["mp4","mov"], key=f"vid_{idx}")
        # Save image
        if img_file:
            path = os.path.join(MEDIA_FOLDER, img_file.name)
            with open(path, "wb") as f:
                f.write(img_file.getbuffer())
            existing = df_main.at[idx, "image"]
            df_main.at[idx, "image"] = f"{existing}|{img_file.name}" if existing else img_file.name
        # Save video
        if vid_file:
            path = os.path.join(MEDIA_FOLDER, vid_file.name)
            with open(path, "wb") as f:
                f.write(vid_file.getbuffer())
            existing = df_main.at[idx, "video"]
            df_main.at[idx, "video"] = f"{existing}|{vid_file.name}" if existing else vid_file.name

elif page == "🏗️ Architecture Issues (Editable)":
    st.title("🏗️ Edit Architecture Issues")
    st.markdown("💾 Save / Download options are sticky on top")

    # Save/Download buttons
    col1, col2 = st.columns([1,1])
    with col1:
        if st.button("💾 Save Architecture Sheet"):
            save_excel(df_main, df_arch)
            st.success("Architecture Issues saved.")
    with col2:
        st.download_button("⬇ Download Excel", data=open(EXCEL_PATH, "rb").read(), file_name="architecture_issues_updated.xlsx")

    # Data editor
    edited_arch = st.experimental_data_editor(df_arch, num_rows="dynamic", use_container_width=True)
    df_arch = edited_arch.copy()

    # Media upload per row
    st.subheader("Upload Media for Rows")
    for idx in df_arch.index:
        st.markdown(f"**Row {idx+1}: {df_arch.at[idx,'Issue']}**")
        img_file = st.file_uploader(f"Upload Image for row {idx+1}", type=["png","jpg","jpeg"], key=f"arch_img_{idx}")
        vid_file = st.file_uploader(f"Upload Video for row {idx+1}", type=["mp4","mov"], key=f"arch_vid_{idx}")
        # Save image
        if img_file:
            path = os.path.join(MEDIA_FOLDER, img_file.name)
            with open(path, "wb") as f:
                f.write(img_file.getbuffer())
            existing = df_arch.at[idx, "image"]
            df_arch.at[idx, "image"] = f"{existing}|{img_file.name}" if existing else img_file.name
        # Save video
        if vid_file:
            path = os.path.join(MEDIA_FOLDER, vid_file.name)
            with open(path, "wb") as f:
                f.write(vid_file.getbuffer())
            existing = df_arch.at[idx, "video"]
            df_arch.at[idx, "video"] = f"{existing}|{vid_file.name}" if existing else vid_file.name

# ------------------------ USER FEEDBACK ------------------------
elif page == "📝 User Feedback":
    st.title("📝 User Feedback")
    st.subheader("Submit Feedback")
    with st.form("feedback_form", clear_on_submit=True):
        user_name = st.text_input("Your Name")
        feedback_text = st.text_area("Your Feedback")
        fb_img = st.file_uploader("Upload Image (optional)", type=["png","jpg","jpeg"])
        fb_vid = st.file_uploader("Upload Video (optional)", type=["mp4","mov"])
        submitted = st.form_submit_button("Submit Feedback")
        if submitted:
            new_row = {"Timestamp": pd.Timestamp.now(), "User": user_name, "Feedback": feedback_text, "image": "", "video": ""}
            # Save media
            if fb_img:
                path = os.path.join(MEDIA_FOLDER, fb_img.name)
                with open(path, "wb") as f:
                    f.write(fb_img.getbuffer())
                new_row["image"] = fb_img.name
            if fb_vid:
                path = os.path.join(MEDIA_FOLDER, fb_vid.name)
                with open(path, "wb") as f:
                    f.write(fb_vid.getbuffer())
                new_row["video"] = fb_vid.name
            df_feedback = pd.concat([df_feedback, pd.DataFrame([new_row])], ignore_index=True)
            save_feedback(df_feedback)
            st.success("Feedback submitted!")

    # Display feedback table
    st.subheader("All Feedbacks")
    st.dataframe(df_feedback, use_container_width=True)
