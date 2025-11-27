import streamlit as st
import pandas as pd
import os
from io import BytesIO
import plotly.express as px

st.set_page_config(page_title="UAT & Architecture Bug Tracker", layout="wide")
st.title("🧪 Noether IP Status")


# ------------------------ CONFIG ------------------------
EXCEL_PATH = "uat_issues.xlsx"
MEDIA_FOLDER = "media"
FEEDBACK_PATH = "user_feedback.xlsx"
CLIENT_COLUMNS = ["Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo"]

os.makedirs(MEDIA_FOLDER, exist_ok=True)


# ------------------------ UTILITIES ------------------------
@st.cache_data(ttl=5)
def load_excel():
    if not os.path.exists(EXCEL_PATH):
        df_main = pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates",
                                        "Type","Issue", *CLIENT_COLUMNS,
                                        "image","video","remarks","dev status"])

        df_arch = pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates",
                                        "Type","Issue","Status",
                                        "image","video","remarks","dev status"])
        return df_main, df_arch

    xls = pd.ExcelFile(EXCEL_PATH)
    sheet_names = [s.lower() for s in xls.sheet_names]

    df_main = pd.read_excel(EXCEL_PATH,
                            sheet_name=xls.sheet_names[sheet_names.index("uat_issues")]) \
                if "uat_issues" in sheet_names else pd.DataFrame()

    df_arch = pd.read_excel(EXCEL_PATH,
                            sheet_name=xls.sheet_names[sheet_names.index("architecture_issues")]) \
                if "architecture_issues" in sheet_names else pd.DataFrame()

    df_main.columns = df_main.columns.str.strip()
    df_arch.columns = df_arch.columns.str.strip()

    return df_main, df_arch


def save_excel(df_main, df_arch):
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="uat_issues", index=False)
        df_arch.to_excel(writer, sheet_name="architecture_issues", index=False)


def load_feedback():
    return pd.read_excel(FEEDBACK_PATH) if os.path.exists(FEEDBACK_PATH) \
        else pd.DataFrame(columns=["Name","Email","Feedback","Date"])


def save_feedback(df_fb):
    df_fb.to_excel(FEEDBACK_PATH, index=False)


# ------------------------ SESSION STATE INIT ------------------------
if "df_main" not in st.session_state:
    st.session_state.df_main, st.session_state.df_arch = load_excel()

if "df_feedback" not in st.session_state:
    st.session_state.df_feedback = load_feedback()


# ------------------------ SIDEBAR PAGE SELECTOR ------------------------
page = st.sidebar.radio(
    "Select Page",
    ["📊 Dashboard", "📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)", "✉️ User Feedback"]
)


# ------------------------ EXCEL UPLOAD ------------------------
uploaded_file = st.file_uploader("Upload Excel to update tables", type=["xlsx"])

if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = [s.lower() for s in xls.sheet_names]

        if "uat_issues" in sheet_names:
            st.session_state.df_main = pd.read_excel(uploaded_file, sheet_name="uat_issues")

        if "architecture_issues" in sheet_names:
            st.session_state.df_arch = pd.read_excel(uploaded_file, sheet_name="architecture_issues")

        st.success("Excel loaded successfully!")

        required_columns_main = ["Sno.","Date","Issue", *CLIENT_COLUMNS]
        if not all(col in st.session_state.df_main.columns for col in required_columns_main):
            st.warning("Uploaded UAT sheet is missing required columns!")

    except Exception as e:
        st.error(f"Error loading Excel: {e}")


# ======================================================================
#                                DASHBOARD
# ======================================================================
if page == "📊 Dashboard":

    dashboard_type = st.radio("Choose Dashboard", ["UAT Issues", "Architecture Issues"])
    df = st.session_state.df_main.copy() if dashboard_type == "UAT Issues" else st.session_state.df_arch.copy()

    st.header(f"📊 {dashboard_type} Dashboard")

    # -------- FILTERS --------
    type_options = df["Type"].dropna().unique().tolist() if "Type" in df.columns else []
    selected_types = st.multiselect("Filter by Type", type_options, default=type_options)

    if selected_types:
        df = df[df["Type"].isin(selected_types)]

    if dashboard_type == "UAT Issues":
        client_options = [c for c in CLIENT_COLUMNS if c in df.columns]
        selected_clients = st.multiselect("Filter by Resolved Clients", client_options)

        if selected_clients:
            df = df[df[selected_clients].eq("Yes").all(axis=1)]

    else:
        status_options = df["Status"].dropna().unique().tolist() if "Status" in df.columns else []
        selected_status = st.multiselect("Filter by Status", status_options, default=status_options)

        if selected_status:
            df = df[df["Status"].isin(selected_status)]

    # -------- TABLE --------
    columns_to_show = st.multiselect("Select columns to display",
                                     df.columns.tolist(),
                                     default=df.columns.tolist())

    st.dataframe(df[columns_to_show], use_container_width=True)

    # -------- MEDIA VIEWER --------
    with st.expander("📂 Media Viewer"):
        for idx, row in df.iterrows():
            st.markdown(f"**S.No {row.get('Sno.', '')} — {row.get('Issue', '')}**")

            # Images
            for img in set(str(row.get("image", "")).split("|")):
                img = img.strip()
                path = os.path.join(MEDIA_FOLDER, img)
                if img and os.path.exists(path):
                    st.image(path)

            # Videos
            for vid in set(str(row.get("video", "")).split("|")):
                vid = vid.strip()
                path = os.path.join(MEDIA_FOLDER, vid)
                if vid and os.path.exists(path):
                    st.video(path)

    # -------- FIXED CHART BLOCK (SAFE) --------
    st.subheader("📈 Predefined Charts")

    # Type Chart
    if "Type" in df.columns:
        type_counts = df["Type"].dropna().value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]

        if not type_counts.empty:
            fig = px.bar(type_counts, x="Type", y="Count", title="Issues by Type")
            st.plotly_chart(fig)
        else:
            st.info("No data for 'Issues by Type'")

    # Status Chart (Only if exists)
    if "Status" in df.columns:
        status_counts = df["Status"].dropna().value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        if not status_counts.empty:
            fig = px.pie(status_counts, names="Status", values="Count", title="Status Counts")
            st.plotly_chart(fig)
        else:
            st.info("No data for 'Status Counts'")

    # -------- CUSTOM CHARTS --------
    st.subheader("📊 Custom Chart")

    chart_col = st.selectbox("Select column", df.columns.tolist())
    chart_type = st.selectbox("Select chart type", ["Bar", "Pie", "Histogram"])

    try:
        if chart_type == "Bar":
            fig = px.bar(df, x=chart_col, title=f"{chart_col} (Bar Chart)")
        elif chart_type == "Pie":
            fig = px.pie(df, names=chart_col, title=f"{chart_col} (Pie Chart)")
        else:
            fig = px.histogram(df, x=chart_col, title=f"{chart_col} (Histogram)")

        st.plotly_chart(fig)

    except:
        st.warning("Chart cannot be displayed for this column.")


# ======================================================================
#                        UAT ISSUES EDITABLE PAGE
# ======================================================================
elif page == "📋 UAT Issues (Editable)":

    st.header("📋 Edit UAT Issues")

    save_clicked = st.button("💾 Save Changes")

    edited_main = st.experimental_data_editor(
        st.session_state.df_main,
        num_rows="dynamic",
        use_container_width=True
    )

    # ---------------- MEDIA UPLOAD PER ROW ----------------
    for idx in edited_main.index:
        col1, col2 = st.columns(2)

        with col1:
            img_file = st.file_uploader(
                f"Upload Image for row {idx}",
                type=["png", "jpg", "jpeg"],
                key=f"uat_img_{idx}"
            )
            if img_file:
                img_path = os.path.join(MEDIA_FOLDER, img_file.name)
                with open(img_path, "wb") as f:
                    f.write(img_file.getbuffer())

                existing_images = str(edited_main.at[idx, "image"]) if pd.notna(edited_main.at[idx, "image"]) else ""
                updated_images = list(filter(None, existing_images.split("|"))) + [img_file.name]
                edited_main.at[idx, "image"] = "|".join(sorted(set(updated_images)))

        with col2:
            vid_file = st.file_uploader(
                f"Upload Video for row {idx}",
                type=["mp4", "mov"],
                key=f"uat_vid_{idx}"
            )
            if vid_file:
                vid_path = os.path.join(MEDIA_FOLDER, vid_file.name)
                with open(vid_path, "wb") as f:
                    f.write(vid_file.getbuffer())

                existing_videos = str(edited_main.at[idx, "video"]) if pd.notna(edited_main.at[idx, "video"]) else ""
                updated_videos = list(filter(None, existing_videos.split("|"))) + [vid_file.name]
                edited_main.at[idx, "video"] = "|".join(sorted(set(updated_videos)))

    # ---------------- SAVE ----------------
    if save_clicked:
        st.session_state.df_main = edited_main
        save_excel(st.session_state.df_main, st.session_state.df_arch)
        st.success("UAT Issues saved!")


# ======================================================================
#                   ARCHITECTURE ISSUES EDITABLE PAGE
# ======================================================================
elif page == "🏗️ Architecture Issues (Editable)":

    st.header("🏗️ Edit Architecture Issues")

    save_clicked = st.button("💾 Save Changes")

    edited_arch = st.experimental_data_editor(
        st.session_state.df_arch,
        num_rows="dynamic",
        use_container_width=True
    )

    # ---------------- MEDIA UPLOAD PER ROW ----------------
    for idx in edited_arch.index:
        col1, col2 = st.columns(2)

        with col1:
            img_file = st.file_uploader(
                f"Upload Image for row {idx}",
                type=["png", "jpg", "jpeg"],
                key=f"arch_img_{idx}"
            )
            if img_file:
                img_path = os.path.join(MEDIA_FOLDER, img_file.name)
                with open(img_path, "wb") as f:
                    f.write(img_file.getbuffer())

                existing_images = str(edited_arch.at[idx, "image"]) if pd.notna(edited_arch.at[idx, "image"]) else ""
                updated_images = list(filter(None, existing_images.split("|"))) + [img_file.name]
                edited_arch.at[idx, "image"] = "|".join(sorted(set(updated_images)))

        with col2:
            vid_file = st.file_uploader(
                f"Upload Video for row {idx}",
                type=["mp4", "mov"],
                key=f"arch_vid_{idx}"
            )
            if vid_file:
                vid_path = os.path.join(MEDIA_FOLDER, vid_file.name)
                with open(vid_path, "wb") as f:
                    f.write(vid_file.getbuffer())

                existing_videos = str(edited_arch.at[idx, "video"]) if pd.notna(edited_arch.at[idx, "video"]) else ""
                updated_videos = list(filter(None, existing_videos.split("|"))) + [vid_file.name]
                edited_arch.at[idx, "video"] = "|".join(sorted(set(updated_videos)))

    # ---------------- SAVE BUTTON ----------------
    if save_clicked:
        st.session_state.df_arch = edited_arch
        save_excel(st.session_state.df_main, st.session_state.df_arch)
        st.success("Architecture Issues saved!")



# ======================================================================
#                            USER FEEDBACK PAGE
# ======================================================================
elif page == "✉️ User Feedback":

    st.header("✉️ User Feedback")

    with st.form("fb_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        feedback = st.text_area("Feedback")
        submit = st.form_submit_button("Submit")

        if submit:
            st.session_state.df_feedback.loc[len(st.session_state.df_feedback)] = [
                name, email, feedback, pd.Timestamp.now()
            ]
            save_feedback(st.session_state.df_feedback)
            st.success("Feedback submitted!")

    edited_fb = st.experimental_data_editor(
        st.session_state.df_feedback, num_rows="dynamic"
    )

    if st.button("💾 Save Feedback Changes"):
        st.session_state.df_feedback = edited_fb
        save_feedback(st.session_state.df_feedback)
        st.success("Changes saved!")

    buf = BytesIO()
    st.session_state.df_feedback.to_excel(buf, index=False)
    buf.seek(0)

    st.download_button("⬇ Download Feedback", buf, "user_feedback.xlsx")
