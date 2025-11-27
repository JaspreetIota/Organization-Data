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
                                        "Type","Issue", *CLIENT_COLUMNS, "image","video","remarks","dev status"])
        df_arch = pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates",
                                        "Type","Issue","Status","image","video","remarks","dev status"])
        return df_main, df_arch
    xls = pd.ExcelFile(EXCEL_PATH)
    sheet_names = [s.lower() for s in xls.sheet_names]
    df_main = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("uat_issues")]) if "uat_issues" in sheet_names else pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates","Type","Issue", *CLIENT_COLUMNS, "image","video","remarks","dev status"])
    df_arch = pd.read_excel(EXCEL_PATH, sheet_name=xls.sheet_names[sheet_names.index("architecture_issues")]) if "architecture_issues" in sheet_names else pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates","Type","Issue","Status","image","video","remarks","dev status"])
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
    return pd.DataFrame(columns=["Name","Email","Feedback","Date"])

def save_feedback(df_fb):
    df_fb.to_excel(FEEDBACK_PATH, index=False)

# ------------------------ SESSION STATE INIT ------------------------
if "df_main" not in st.session_state:
    st.session_state.df_main, st.session_state.df_arch = load_excel()
if "df_feedback" not in st.session_state:
    st.session_state.df_feedback = load_feedback()

# ------------------------ APP CONFIG ------------------------
page = st.sidebar.radio("Select Page", ["📊 Dashboard", "📋 UAT Issues (Editable)", "🏗️ Architecture Issues (Editable)", "✉️ User Feedback"])

# ------------------------ EXCEL UPLOAD ------------------------
uploaded_file = st.file_uploader("Upload Excel to update tables", type=["xlsx"])
if uploaded_file:
    try:
        xls = pd.ExcelFile(uploaded_file)
        if "uat_issues" in [s.lower() for s in xls.sheet_names]:
            st.session_state.df_main = pd.read_excel(uploaded_file, sheet_name="uat_issues")
        if "architecture_issues" in [s.lower() for s in xls.sheet_names]:
            st.session_state.df_arch = pd.read_excel(uploaded_file, sheet_name="architecture_issues")
        st.success("Excel loaded successfully! Tables updated.")
        
        # Validation
        required_columns_main = ["Sno.","Date","Issue", *CLIENT_COLUMNS]
        if not all(col in st.session_state.df_main.columns for col in required_columns_main):
            st.warning("Uploaded UAT sheet is missing required columns!")

    except Exception as e:
        st.error(f"Error loading Excel: {e}")

# ------------------------ DASHBOARD ------------------------
if page == "📊 Dashboard":
    dashboard_type = st.radio("Choose Dashboard", ["UAT Issues", "Architecture Issues"])
    df = st.session_state.df_main.copy() if dashboard_type == "UAT Issues" else st.session_state.df_arch.copy()
    
    st.header(f"📊 {dashboard_type} Dashboard")
    
    # Filters
    type_options = df["Type"].dropna().unique().tolist() if "Type" in df.columns else []
    selected_types = st.multiselect("Filter by Type", type_options, default=type_options)
    if dashboard_type == "UAT Issues":
        client_options = [c for c in CLIENT_COLUMNS if c in df.columns]
        selected_clients = st.multiselect("Filter by Resolved Clients", client_options, default=[])
    else:
        status_options = df["Status"].dropna().unique().tolist() if "Status" in df.columns else []
        selected_status = st.multiselect("Filter by Status", status_options, default=status_options)
    
    if selected_types: df = df[df["Type"].isin(selected_types)]
    if dashboard_type == "UAT Issues" and selected_clients:
        df = df[df[selected_clients].eq("Yes").all(axis=1)]
    if dashboard_type != "UAT Issues" and selected_status:
        df = df[df["Status"].isin(selected_status)]
    
    # Column selection
    columns_to_show = st.multiselect("Select columns to display", df.columns.tolist(), default=df.columns.tolist())
    st.dataframe(df[columns_to_show] if columns_to_show else df, use_container_width=True)
    
    # Media Viewer
    with st.expander("📂 Media Viewer (Expand to see all images/videos)"):
        for idx, row in df.iterrows():
            st.markdown(f"**S.No: {row.get('Sno.', '')} | Issue: {row.get('Issue','')}**")
            for img in set(str(row.get("image","")).split("|")):
                img = img.strip()
                if img and os.path.exists(os.path.join(MEDIA_FOLDER, img)):
                    st.image(os.path.join(MEDIA_FOLDER, img), caption=img, use_column_width=True)
            for vid in set(str(row.get("video","")).split("|")):
                vid = vid.strip()
                if vid and os.path.exists(os.path.join(MEDIA_FOLDER, vid)):
                    st.video(os.path.join(MEDIA_FOLDER, vid))
    
    # Predefined Charts
    st.subheader("Predefined Charts")
    if "Type" in df.columns and not df.empty:
        fig = px.bar(df['Type'].value_counts().reset_index().rename(columns={'index':'Type','Type':'Count'}), x='Type', y='Count', title='Issues by Type')
        st.plotly_chart(fig, use_container_width=True)
    if "Status" in df.columns and not df.empty:
        fig = px.pie(df['Status'].value_counts().reset_index().rename(columns={'index':'Status','Status':'Count'}), names='Status', values='Count', title='Status Counts')
        st.plotly_chart(fig, use_container_width=True)
    
    # Custom Charts
    st.subheader("Custom Chart")
    chart_col = st.selectbox("Select column for chart", df.columns.tolist(), key=f"{dashboard_type}_chart_col")
    chart_type = st.selectbox("Select chart type", ["Bar","Pie","Histogram"], key=f"{dashboard_type}_chart_type")
    if chart_col:
        try:
            if chart_type=="Bar": fig = px.bar(df, x=chart_col, title=f"Bar Chart: {chart_col}")
            elif chart_type=="Pie": fig = px.pie(df, names=chart_col, title=f"Pie Chart: {chart_col}")
            elif chart_type=="Histogram": fig = px.histogram(df, x=chart_col, title=f"Histogram: {chart_col}")
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Cannot generate chart for column '{chart_col}': {e}")

# ------------------------ UAT EDITABLE ------------------------
elif page == "📋 UAT Issues (Editable)":
    st.header("📋 Edit UAT Issues")
    
    # Sticky Save button
    st.markdown("""<style>.sticky-save {position: sticky; top: 0; z-index: 1000; background-color: white; padding: 10px; border-bottom: 1px solid #ddd;}</style>""", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="sticky-save">', unsafe_allow_html=True)
        save_clicked = st.button("💾 Save Changes")
        st.markdown('</div>', unsafe_allow_html=True)
    
    edited_main = st.experimental_data_editor(st.session_state.df_main, num_rows="dynamic", use_container_width=True)
    
    # Media upload
    for idx in edited_main.index:
        img_file = st.file_uploader(f"Upload Image for row {idx+1}", type=["png","jpg","jpeg"], key=f"img_{idx}")
        vid_file = st.file_uploader(f"Upload Video for row {idx+1}", type=["mp4","mov"], key=f"vid_{idx}")
        if img_file:
            path = os.path.join(MEDIA_FOLDER, img_file.name)
            with open(path,"wb") as f: f.write(img_file.getbuffer())
            current_imgs = str(edited_main.at[idx,"image"]) if pd.notna(edited_main.at[idx,"image"]) else ""
            edited_main.at[idx,"image"] = "|".join(list(set(current_imgs.split("|")+ [img_file.name])))
        if vid_file:
            path = os.path.join(MEDIA_FOLDER, vid_file.name)
            with open(path,"wb") as f: f.write(vid_file.getbuffer())
            current_vids = str(edited_main.at[idx,"video"]) if pd.notna(edited_main.at[idx,"video"]) else ""
            edited_main.at[idx,"video"] = "|".join(list(set(current_vids.split("|")+ [vid_file.name])))
    
    if save_clicked:
        st.session_state.df_main = edited_main
        save_excel(st.session_state.df_main, st.session_state.df_arch)
        st.success("UAT Issues saved successfully!")

# ------------------------ ARCHITECTURE EDITABLE ------------------------
elif page == "🏗️ Architecture Issues (Editable)":
    st.header("🏗️ Edit Architecture Issues")
    
    # Sticky Save button
    st.markdown("""<style>.sticky-save {position: sticky; top: 0; z-index: 1000; background-color: white; padding: 10px; border-bottom: 1px solid #ddd;}</style>""", unsafe_allow_html=True)
    with st.container():
        st.markdown('<div class="sticky-save">', unsafe_allow_html=True)
        save_clicked = st.button("💾 Save Changes")
        st.markdown('</div>', unsafe_allow_html=True)
    
    edited_arch = st.experimental_data_editor(st.session_state.df_arch, num_rows="dynamic", use_container_width=True)
    
    # Media upload
    for idx in edited_arch.index:
        img_file = st.file_uploader(f"Upload Image for row {idx+1}", type=["png","jpg","jpeg"], key=f"arch_img_{idx}")
        vid_file = st.file_uploader(f"Upload Video for row {idx+1}", type=["mp4","mov"], key=f"arch_vid_{idx}")
        if img_file:
            path = os.path.join(MEDIA_FOLDER, img_file.name)
            with open(path,"wb") as f: f.write(img_file.getbuffer())
            current_imgs = str(edited_arch.at[idx,"image"]) if pd.notna(edited_arch.at[idx,"image"]) else ""
            edited_arch.at[idx,"image"] = "|".join(list(set(current_imgs.split("|")+ [img_file.name])))
        if vid_file:
            path = os.path.join(MEDIA_FOLDER, vid_file.name)
            with open(path,"wb") as f: f.write(vid_file.getbuffer())
            current_vids = str(edited_arch.at[idx,"video"]) if pd.notna(edited_arch.at[idx,"video"]) else ""
            edited_arch.at[idx,"video"] = "|".join(list(set(current_vids.split("|")+ [vid_file.name])))
    
    if save_clicked:
        st.session_state.df_arch = edited_arch
        save_excel(st.session_state.df_main, st.session_state.df_arch)
        st.success("Architecture Issues saved successfully!")

# ------------------------ USER FEEDBACK ------------------------
elif page == "✉️ User Feedback":
    st.header("✉️ User Feedback")
    
    with st.form("feedback_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        feedback = st.text_area("Feedback")
        submitted = st.form_submit_button("Submit")
        if submitted:
            st.session_state.df_feedback = st.session_state.df_feedback.append({
                "Name": name, "Email": email, "Feedback": feedback, "Date": pd.Timestamp.now()
            }, ignore_index=True)
            save_feedback(st.session_state.df_feedback)
            st.success("Feedback saved successfully!")
    
    st.subheader("Edit Submitted Feedback")
    edited_feedback = st.experimental_data_editor(st.session_state.df_feedback, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Save Feedback Changes"):
        st.session_state.df_feedback = edited_feedback
        save_feedback(st.session_state.df_feedback)
        st.success("Feedback edits saved successfully!")
    
    download_buffer = BytesIO()
    st.session_state.df_feedback.to_excel(download_buffer, index=False)
    download_buffer.seek(0)
    st.download_button("⬇ Download Feedback Excel", data=download_buffer.getvalue(), file_name="user_feedback.xlsx")
