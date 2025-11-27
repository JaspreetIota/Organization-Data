import streamlit as st
import pandas as pd
import os
from io import BytesIO
import plotly.express as px
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, DataReturnMode

EXCEL_PATH = "uat_issues.xlsx"
MEDIA_FOLDER = "media"
FEEDBACK_PATH = "user_feedback.xlsx"

CLIENT_COLUMNS = ["Portfolio Demo", "Diabetes", "TMW", "MDR", "EDL", "STF", "IPRG Demo"]

# ------------------------ UTILITIES ------------------------
os.makedirs(MEDIA_FOLDER, exist_ok=True)

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
    df_main = pd.read_excel(EXCEL_PATH, sheet_name="uat_issues") if "uat_issues" in sheet_names else pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates","Type","Issue", *CLIENT_COLUMNS, "image","video","remarks","dev status"])
    df_arch = pd.read_excel(EXCEL_PATH, sheet_name="architecture_issues") if "architecture_issues" in sheet_names else pd.DataFrame(columns=["Sno.","Date","Repetitive Count","Repetitive Dates","Type","Issue","Status","image","video","remarks","dev status"])
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
    st.header("📊 Dashboard")
    # Existing dashboard code with Plotly charts etc.
    st.info("Dashboard code goes here...")  # Keep your existing dashboard code

# ------------------------ UAT ISSUES ------------------------
elif page == "📋 UAT Issues (Editable)":
    st.header("📋 Edit UAT Issues")

    # Build AgGrid options
    gb = GridOptionsBuilder.from_dataframe(df_main)
    gb.configure_default_column(editable=True, filter=True, sortable=True)
    gb.configure_selection('single')
    grid_options = gb.build()

    # Display editable grid
    grid_response = AgGrid(
        df_main,
        gridOptions=grid_options,
        editable=True,
        height=500,
        width='100%',
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.MODEL_CHANGED
    )
    edited_main = grid_response['data']

    if st.button("💾 Save UAT Changes"):
        save_excel(edited_main, df_arch)
        st.success("UAT Issues saved successfully!")

# ------------------------ ARCHITECTURE ISSUES ------------------------
elif page == "🏗️ Architecture Issues (Editable)":
    st.header("🏗️ Edit Architecture Issues")

    gb = GridOptionsBuilder.from_dataframe(df_arch)
    gb.configure_default_column(editable=True, filter=True, sortable=True)
    gb.configure_selection('single')
    grid_options = gb.build()

    grid_response = AgGrid(
        df_arch,
        gridOptions=grid_options,
        editable=True,
        height=500,
        width='100%',
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.MODEL_CHANGED
    )
    edited_arch = grid_response['data']

    if st.button("💾 Save Architecture Changes"):
        save_excel(df_main, edited_arch)
        st.success("Architecture Issues saved successfully!")

# ------------------------ USER FEEDBACK ------------------------
elif page == "✉️ User Feedback":
    st.header("✉️ User Feedback")
    
    # Feedback submission form
    with st.form("feedback_form"):
        name = st.text_input("Name")
        email = st.text_input("Email")
        feedback = st.text_area("Feedback")
        submitted = st.form_submit_button("Submit")
        if submitted:
            df_feedback = pd.concat([df_feedback, pd.DataFrame([{"Name": name, "Email": email, "Feedback": feedback, "Date": pd.Timestamp.now()}])], ignore_index=True)
            save_feedback(df_feedback)
            st.success("Feedback saved successfully!")

    st.subheader("Edit Submitted Feedback")
    gb = GridOptionsBuilder.from_dataframe(df_feedback)
    gb.configure_default_column(editable=True, filter=True, sortable=True)
    gb.configure_selection('single')
    grid_options = gb.build()

    grid_response = AgGrid(
        df_feedback,
        gridOptions=grid_options,
        editable=True,
        height=500,
        width='100%',
        data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
        update_mode=GridUpdateMode.MODEL_CHANGED
    )
    edited_feedback = grid_response['data']

    if st.button("💾 Save Feedback Changes"):
        save_feedback(edited_feedback)
        st.success("Feedback edits saved successfully!")
