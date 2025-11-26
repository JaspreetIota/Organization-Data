import streamlit as st
import pandas as pd
import os
from io import BytesIO
import plotly.express as px

EXCEL_PATH = "uat_issues.xlsx"
MEDIA_FOLDER = "media"
FEEDBACK_PATH = "user_feedback.xlsx"

CLIENT_COLUMNS = ["Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo"]

# ------------------------ UTILITIES ------------------------
os.makedirs(MEDIA_FOLDER, exist_ok=True)

@st.cache_data(ttl=5)
def load_excel():
    if not os.path.exists(EXCEL_PATH):
        st.warning(f"Excel file {EXCEL_PATH} not found. Creating empty sheets.")
        df_main = pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates",
                                        "Type","Issue", *CLIENT_COLUMNS, "image","video","remarks","dev status"])
        df_arch = pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates",
                                        "Type","Issue","Status","image","video","remarks","dev status"])
        return df_main, df_arch
    xls = pd.ExcelFile(EXCEL_PATH)
    sheet_names = [s.lower() for s in xls.sheet_names]
    if "uat_issues" in sheet_names:
        df_main = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("uat_issues")])
    else:
        df_main = pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates",
                                        "Type","Issue", *CLIENT_COLUMNS, "image","video","remarks","dev status"])
    if "architecture_issues" in sheet_names:
        df_arch = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("architecture_issues")])
    else:
        df_arch = pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates",
                                        "Type","Issue","Status","image","video","remarks","dev status"])
    df_main.columns = df_main.columns.str.strip()
    df_arch.columns = df_arch.columns.str.strip()
    return df_main, df_arch

def save_excel(df_main, df_arch):
    with pd.ExcelWriter(EXCEL_PATH, engine="openpyxl") as writer:
        df_main.to_excel(writer, sheet_name="uat_issues", index=False)
        df_arch.to_excel(writer, sheet_name="architecture_issues", index=False)

def load_feedback():
    if os.path.exists(FEEDBACK_PATH):
        return pd.read_excel(FEEDBACK_PATH)
    else:
        return pd.DataFrame(columns=["Name","Email","Feedback","Date"])

def save_feedback(df_fb):
    df_fb.to_excel(FEEDBACK_PATH, index=False)

# ------------------------ APP CONFIG ------------------------
st.set_page_config(page_title="UAT & Architecture Bug Tracker", layout="wide")
st.title("🧪 Noether IP Status")

df_main, df_arch = load_excel()
df_feedback = load_feedback()

page = st.sidebar.radio("Select Page", ["📊 Dashboard", "📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)", "✉️ User Feedback"])

# ------------------------ DASHBOARD ------------------------
if page == "📊 Dashboard":
    dashboard_type = st.radio("Choose Dashboard", ["UAT Issues", "Architecture Issues"])

    if dashboard_type == "UAT Issues":
        st.header("📊 UAT Issues Dashboard")
        df = df_main.copy()
        # Filters
        type_options = df["Type"].dropna().unique().tolist() if "Type" in df.columns else []
        selected_types = st.multiselect("Filter by Type", type_options, default=type_options)
        client_options = [c for c in CLIENT_COLUMNS if c in df.columns]
        selected_clients = st.multiselect("Filter by Resolved Clients", client_options, default=client_options)

        if selected_types:
            df = df[df["Type"].isin(selected_types)]
        if selected_clients:
            df = df[df[selected_clients].eq("Yes").all(axis=1)]

    else:
        st.header("🏗️ Architecture Issues Dashboard")
        df = df_arch.copy()
        type_options = df["Type"].dropna().unique().tolist() if "Type" in df.columns else []
        selected_types = st.multiselect("Filter by Type", type_options, default=type_options)
        status_options = df["Status"].dropna().unique().tolist() if "Status" in df.columns else []
        selected_status = st.multiselect("Filter by Status", status_options, default=status_options)
        if selected_types:
            df = df[df["Type"].isin(selected_types)]
        if selected_status:
            df = df[df["Status"].isin(selected_status)]

    # Column selection
    columns_to_show = st.multiselect("Select columns to display", df.columns.tolist(), default=df.columns.tolist())
    df_display = df[columns_to_show] if columns_to_show else df
    st.dataframe(df_display, use_container_width=True)

    # Media Viewer
    with st.expander("📂 Media Viewer (Expand to see all images/videos)"):
        for idx, row in df.iterrows():
            title = f"S.No: {row.get('Sno.', '')} | Issue: {row.get('Issue','')}"
            st.markdown(f"**{title}**")
            # Images
            images = list(set(str(row.get("image","")).split("|")))
            for img in images:
                img = img.strip()
                if img:
                    img_path = os.path.join(MEDIA_FOLDER, img)
                    if os.path.exists(img_path):
                        st.image(img_path, caption=img, use_column_width=True)
            # Videos
            videos = list(set(str(row.get("video","")).split("|")))
            for vid in videos:
                vid = vid.strip()
                if vid:
                    vid_path = os.path.join(MEDIA_FOLDER, vid)
                    if os.path.exists(vid_path):
                        st.video(vid_path)

    # Predefined charts
    st.subheader("Predefined Charts")
    if "Type" in df.columns and not df.empty:
        type_counts = df['Type'].value_counts().reset_index()
        type_counts.columns = ['Type','Count']
        fig = px.bar(type_counts, x='Type', y='Count', title='Issues by Type')
        st.plotly_chart(fig, use_container_width=True)
    if "Status" in df.columns and "Status" in df.columns and not df.empty:
        status_counts = df['Status'].value_counts().reset_index()
        status_counts.columns = ['Status','Count']
        fig = px.pie(status_counts, names='Status', values='Count', title='Status Counts')
        st.plotly_chart(fig, use_container_width=True)

    # Custom Charts
    st.subheader("Custom Chart")
    chart_col = st.selectbox("Select column for chart", df.columns.tolist(), key=f"{dashboard_type}_chart_col")
    chart_type = st.selectbox("Select chart type", ["Bar","Pie","Histogram"], key=f"{dashboard_type}_chart_type")
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
            st.warning(f"Cannot generate chart for column '{chart_col}': {e}")

# ------------------------ EDITABLE SHEETS ------------------------
elif page == "📋 UAT Issues (Editable)":
    st.header("📋 Edit UAT Issues")
    st.markdown("💾 **Save automatically** on any edit or media upload.")
    edited_main = st.experimental_data_editor(df_main, num_rows="dynamic", use_container_width=True)

    for idx in edited_main.index:
        st.markdown(f"**Row {idx+1}: {edited_main.at[idx,'Issue']}**")
        img_file = st.file_uploader(f"Upload Image for row {idx+1}", type=["png","jpg","jpeg"], key=f"img_{idx}")
        vid_file = st.file_uploader(f"Upload Video for row {idx+1}", type=["mp4","mov"], key=f"vid_{idx}")
        # Image handling
        if img_file:
            path = os.path.join(MEDIA_FOLDER, img_file.name)
            with open(path,"wb") as f:
                f.write(img_file.getbuffer())
            current_imgs = str(edited_main.at[idx,"image"]) if pd.notna(edited_main.at[idx,"image"]) else ""
            imgs = list(set(current_imgs.split("|") + [img_file.name]))
            edited_main.at[idx,"image"] = "|".join([i for i in imgs if i])
        # Video handling
        if vid_file:
            path = os.path.join(MEDIA_FOLDER, vid_file.name)
            with open(path,"wb") as f:
                f.write(vid_file.getbuffer())
            current_vids = str(edited_main.at[idx,"video"]) if pd.notna(edited_main.at[idx,"video"]) else ""
            vids = list(set(current_vids.split("|") + [vid_file.name]))
            edited_main.at[idx,"video"] = "|".join([v for v in vids if v])

    save_excel(edited_main, df_arch)
    st.success("UAT Issues saved permanently.")
    st.download_button("⬇ Download UAT Excel", data=open(EXCEL_PATH,"rb").read(), file_name="uat_issues_updated.xlsx")

elif page == "🏗️ Architecture Issues (Editable)":
    st.header("🏗️ Edit Architecture Issues")
    st.markdown("💾 **Save automatically** on any edit or media upload.")
    edited_arch = st.experimental_data_editor(df_arch, num_rows="dynamic", use_container_width=True)

    for idx in edited_arch.index:
        st.markdown(f"**Row {idx+1}: {edited_arch.at[idx,'Issue']}**")
        img_file = st.file_uploader(f"Upload Image for row {idx+1}", type=["png","jpg","jpeg"], key=f"arch_img_{idx}")
        vid_file = st.file_uploader(f"Upload Video for row {idx+1}", type=["mp4","mov"], key=f"arch_vid_{idx}")
        if img_file:
            path = os.path.join(MEDIA_FOLDER, img_file.name)
            with open(path,"wb") as f:
                f.write(img_file.getbuffer())
            current_imgs = str(edited_arch.at[idx,"image"]) if pd.notna(edited_arch.at[idx,"image"]) else ""
            imgs = list(set(current_imgs.split("|") + [img_file.name]))
            edited_arch.at[idx,"image"] = "|".join([i for i in imgs if i])
        if vid_file:
            path = os.path.join(MEDIA_FOLDER, vid_file.name)
            with open(path,"wb") as f:
                f.write(vid_file.getbuffer())
            current_vids = str(edited_arch.at[idx,"video"]) if pd.notna(edited_arch.at[idx,"video"]) else ""
            vids = list(set(current_vids.split("|") + [vid_file.name]))
            edited_arch.at[idx,"video"] = "|".join([v for v in vids if v])

    save_excel(df_main, edited_arch)
    st.success("Architecture Issues saved permanently.")
    st.download_button("⬇ Download Architecture Excel", data=open(EXCEL_PATH,"rb").read(), file_name="architecture_issues_updated.xlsx")

# ------------------------ USER FEEDBACK ------------------------
elif page == "✉️ User Feedback":
    st.header("✉️ User Feedback")
    with st.form("feedback_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        feedback = st.text_area("Feedback")
        submitted = st.form_submit_button("Submit")
        if submitted:
            df_feedback = df_feedback.append({"Name":name,"Email":email,"Feedback":feedback,"Date":pd.Timestamp.now()}, ignore_index=True)
            save_feedback(df_feedback)
            st.success("Feedback saved successfully!")

    st.subheader("All Feedbacks")
    st.dataframe(df_feedback, use_container_width=True)
