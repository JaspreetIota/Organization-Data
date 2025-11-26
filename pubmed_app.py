import streamlit as st
import pandas as pd
import os
from io import BytesIO
import plotly.express as px

EXCEL_PATH = "uat_issues.xlsx"
MEDIA_FOLDER = "media"
FEEDBACK_FILE = "user_feedback.xlsx"
CLIENT_COLUMNS = ["Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo"]

st.set_page_config(page_title="UAT & Architecture Bug Tracker", layout="wide")
os.makedirs(MEDIA_FOLDER, exist_ok=True)

# ------------------------ LOAD / INIT DATA ------------------------
def load_or_init_excel():
    if "df_main" not in st.session_state:
        if os.path.exists(EXCEL_PATH):
            xls = pd.ExcelFile(EXCEL_PATH)
            df_main = pd.read_excel(EXCEL_PATH, sheet_name="uat_issues") if "uat_issues" in [s.lower() for s in xls.sheet_names] else pd.DataFrame()
            df_arch = pd.read_excel(EXCEL_PATH, sheet_name="architecture_issues") if "architecture_issues" in [s.lower() for s in xls.sheet_names] else pd.DataFrame()
        else:
            df_main = pd.DataFrame(columns=["Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue", *CLIENT_COLUMNS, "image", "video", "remarks", "dev status"])
            df_arch = pd.DataFrame(columns=["Sno.", "Date", "Repetitive Count", "Repetitive Dates", "Type", "Issue", "Status", "image", "video", "remarks", "dev status"])
        for df in [df_main, df_arch]:
            for col in ["image", "video"]:
                if col not in df.columns:
                    df[col] = ""
        st.session_state.df_main = df_main
        st.session_state.df_arch = df_arch

    if "df_feedback" not in st.session_state:
        if os.path.exists(FEEDBACK_FILE):
            st.session_state.df_feedback = pd.read_excel(FEEDBACK_FILE)
        else:
            st.session_state.df_feedback = pd.DataFrame(columns=["Timestamp","User","Feedback","image","video"])

load_or_init_excel()

# ------------------------ SAVE FUNCTIONS ------------------------
def save_excel():
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        st.session_state.df_main.to_excel(writer, sheet_name="uat_issues", index=False)
        st.session_state.df_arch.to_excel(writer, sheet_name="architecture_issues", index=False)

def save_feedback():
    st.session_state.df_feedback.to_excel(FEEDBACK_FILE, index=False)

# ------------------------ SIDEBAR ------------------------
page = st.sidebar.radio("Select Page", ["📊 Dashboard", "📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)", "📝 User Feedback"])

# ------------------------ DASHBOARD ------------------------
if page == "📊 Dashboard":
    st.title("📊 Bug Tracker Dashboard")
    dashboard_type = st.radio("Select Dashboard", ["UAT Issues", "Architecture Issues"])
    df = st.session_state.df_main if dashboard_type == "UAT Issues" else st.session_state.df_arch

    if df.empty:
        st.warning("No data available.")
    else:
        # Filters
        if "Type" in df.columns:
            type_options = df["Type"].dropna().unique().tolist()
            selected_types = st.multiselect("Filter by Type", type_options, default=type_options)
            df = df[df["Type"].isin(selected_types)] if selected_types else df
        if dashboard_type=="UAT Issues":
            client_options = [c for c in CLIENT_COLUMNS if c in df.columns]
            selected_clients = st.multiselect("Filter by Resolved Clients", client_options, default=client_options)
            if selected_clients:
                df = df[df[selected_clients].eq("Yes").all(axis=1)]
        elif dashboard_type=="Architecture Issues" and "Status" in df.columns:
            status_options = df["Status"].dropna().unique().tolist()
            selected_status = st.multiselect("Filter by Status", status_options, default=status_options)
            if selected_status:
                df = df[df["Status"].isin(selected_status)]

        # Show table
        st.dataframe(df, use_container_width=True)

        # Media Viewer
        with st.expander("📁 Expandable Media Viewer"):
            for idx, row in df.iterrows():
                st.markdown(f"**S.No: {row.get('Sno.', '')} | Issue: {row.get('Issue', '')}**")
                if pd.notna(row.get("image")) and row.get("image") != "":
                    for img in str(row["image"]).split("|"):
                        img_path = os.path.join(MEDIA_FOLDER, img.strip())
                        if os.path.exists(img_path):
                            st.image(img_path, caption=img, use_column_width=True)
                if pd.notna(row.get("video")) and row.get("video") != "":
                    for vid in str(row["video"]).split("|"):
                        vid_path = os.path.join(MEDIA_FOLDER, vid.strip())
                        if os.path.exists(vid_path):
                            st.video(vid_path)

        # Predefined Charts
        st.subheader("Predefined Charts")
        if "Type" in df.columns:
            type_counts = df["Type"].value_counts().reset_index()
            type_counts.columns = ["Type","Count"]
            st.plotly_chart(px.bar(type_counts,x="Type",y="Count",title="Issues by Type"), use_container_width=True)
        if dashboard_type=="Architecture Issues" and "Status" in df.columns:
            status_counts = df["Status"].value_counts().reset_index()
            status_counts.columns = ["Status","Count"]
            st.plotly_chart(px.pie(status_counts,names="Status",values="Count",title="Status Distribution"), use_container_width=True)

# ------------------------ EDITABLE UAT / ARCH ------------------------
elif page in ["📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)"]:
    is_uat = page=="📋 UAT Issues (Editable)"
    df_name = "df_main" if is_uat else "df_arch"
    df = st.session_state[df_name]

    st.title(f"{page}")

    # Sticky Save & Download
    col1,col2 = st.columns([1,1])
    with col1:
        if st.button("💾 Save Sheet"):
            save_excel()
            st.success("Saved!")
    with col2:
        st.download_button("⬇ Download Excel", data=open(EXCEL_PATH,"rb").read(), file_name=f"{df_name}_updated.xlsx")

    # Editable table
    edited = st.experimental_data_editor(df, num_rows="dynamic", use_container_width=True)
    st.session_state[df_name] = edited.copy()
    save_excel()  # Auto-save after edits

    # Upload media per row
    st.subheader("Upload Media per Row")
    for idx in edited.index:
        st.markdown(f"**Row {idx+1}: {edited.at[idx,'Issue']}**")
        img_file = st.file_uploader(f"Image for row {idx+1}", type=["png","jpg","jpeg"], key=f"{df_name}_img_{idx}")
        vid_file = st.file_uploader(f"Video for row {idx+1}", type=["mp4","mov"], key=f"{df_name}_vid_{idx}")
        if img_file:
            path = os.path.join(MEDIA_FOLDER,img_file.name)
            with open(path,"wb") as f: f.write(img_file.getbuffer())
            current = edited.at[idx,"image"]
            edited.at[idx,"image"] = f"{current}|{img_file.name}" if current else img_file.name
        if vid_file:
            path = os.path.join(MEDIA_FOLDER,vid_file.name)
            with open(path,"wb") as f: f.write(vid_file.getbuffer())
            current = edited.at[idx,"video"]
            edited.at[idx,"video"] = f"{current}|{vid_file.name}" if current else vid_file.name
        st.session_state[df_name] = edited.copy()
        save_excel()  # Auto-save

# ------------------------ USER FEEDBACK ------------------------
elif page == "📝 User Feedback":
    st.title("📝 User Feedback")
    with st.form("feedback_form", clear_on_submit=True):
        user_name = st.text_input("Your Name")
        feedback_text = st.text_area("Your Feedback")
        fb_img = st.file_uploader("Image (optional)", type=["png","jpg","jpeg"])
        fb_vid = st.file_uploader("Video (optional)", type=["mp4","mov"])
        submitted = st.form_submit_button("Submit Feedback")
        if submitted:
            new_row = {"Timestamp": pd.Timestamp.now(), "User": user_name, "Feedback": feedback_text, "image":"","video":""}
            if fb_img:
                path = os.path.join(MEDIA_FOLDER,fb_img.name)
                with open(path,"wb") as f: f.write(fb_img.getbuffer())
                new_row["image"]=fb_img.name
            if fb_vid:
                path = os.path.join(MEDIA_FOLDER,fb_vid.name)
                with open(path,"wb") as f: f.write(fb_vid.getbuffer())
                new_row["video"]=fb_vid.name
            st.session_state.df_feedback = pd.concat([st.session_state.df_feedback,pd.DataFrame([new_row])], ignore_index=True)
            save_feedback()
            st.success("Feedback submitted!")

    st.subheader("All Feedbacks")
    st.dataframe(st.session_state.df_feedback, use_container_width=True)
