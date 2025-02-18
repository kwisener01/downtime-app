import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import pytz  # Timezone handling
import speech_recognition as sr  # Voice input
import json

# Define the scope
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Load credentials from Streamlit Secrets
credentials = Credentials.from_service_account_info(st.secrets["google_sheets"], scopes=scope)

# Authorize gspread
client = gspread.authorize(credentials)

# Set timezone to EST (Eastern Standard Time)
est = pytz.timezone("US/Eastern")

# Append data to Google Sheets
def append_to_google_sheets(data, sheet_name="Project Management", worksheet_name="Personal Productivity"):
    try:
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)  # Use the specific worksheet
        data_as_list = data.values.tolist()
        worksheet.append_rows(data_as_list, table_range="A1")
        st.success("Data appended to Google Sheets!")
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' not found. Ensure it exists and is shared with the service account.")

# Load data from Google Sheets
def load_from_google_sheets(sheet_name="Project Management", worksheet_name="Personal Productivity"):
    try:
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        data = pd.DataFrame(worksheet.get_all_records())
        return data
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' not found. Ensure it exists and is shared with the service account.")
        return pd.DataFrame()
    except gspread.exceptions.APIError as e:
        st.error(f"Google Sheets API error: {str(e)}. Please check access permissions and API quota.")
        return pd.DataFrame()
    try:
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)  # Use the specific worksheet
        data = pd.DataFrame(worksheet.get_all_records())
        return data
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' not found. Ensure it exists and is shared with the service account.")
        return pd.DataFrame()

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Time", "Process Name", "Downtime Reason", "Action Taken", "Root Cause", "Time to Resolve (Minutes)", "Resolved (Y/N)"])

# App title
st.title("Operations Management Assistant")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Downtime Issues", "KPI Dashboard", "Personal Productivity"])

### Downtime Tracking ###
with tab1:
    st.header("Enter Downtime Issue")
    with st.form("data_entry_form", clear_on_submit=True):
        today_date = st.date_input("Date", value=date.today())
        current_time_est = datetime.now().astimezone(est).strftime("%H:%M:%S")
        defect_time = st.text_input("Time (HH:MM:SS)", value=current_time_est)
        process_name = st.text_input("Process Name")
        downtime_reason = st.text_input("Downtime Reason")
        action_taken = st.text_input("Action Taken")
        root_cause = st.text_input("Root Cause")
        time_to_resolve = st.number_input("Time to Resolve (Minutes)", min_value=0, step=1)
        resolved = st.selectbox("Resolved?", ["Y", "N"])
        submitted = st.form_submit_button("Add Data")
        if submitted:
            new_row = {"Date": today_date.strftime("%Y-%m-%d"), "Time": defect_time, "Process Name": process_name, "Downtime Reason": downtime_reason, "Action Taken": action_taken, "Root Cause": root_cause, "Time to Resolve (Minutes)": time_to_resolve, "Resolved (Y/N)": resolved}
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
            append_to_google_sheets(pd.DataFrame([new_row]), "Project Management", "Downtime Issues")
    st.subheader("Current Data")
    
    st.subheader("📅 View Downtime Trends")
    
    
    downtime_data = load_from_google_sheets("Project Management", "Downtime Issues")
    if not downtime_data.empty:
        downtime_data["Date"] = pd.to_datetime(downtime_data["Date"])
        process_names = downtime_data["Process Name"].unique().tolist()
    else:
        process_names = []
    selected_process = st.selectbox("Select Process Name", ["All"] + process_names) if process_names else "All"
    
    if selected_process != "All" and 'filtered_data' in locals():
        filtered_data = downtime_data[downtime_data["Process Name"] == selected_process] if not filtered_data.empty else pd.DataFrame()
        filtered_data = filtered_data[filtered_data["Process Name"] == selected_process]
    start_date = st.date_input("Start Date", value=date.today())
    end_date = st.date_input("End Date", value=date.today())
    
    downtime_data = load_from_google_sheets("Project Management", "Downtime Issues")
    if not downtime_data.empty:
        downtime_data["Date"] = pd.to_datetime(downtime_data["Date"])
        filtered_data = downtime_data[(downtime_data["Date"] >= pd.to_datetime(start_date)) & (downtime_data["Date"] <= pd.to_datetime(end_date))]
        st.dataframe(filtered_data)
        
        st.subheader("📊 Downtime Trends")
        
        st.subheader("📈 Downtime Statistics")
        if not filtered_data.empty:
            st.write(f"Total Downtime Entries: {filtered_data.shape[0]}")
            st.write(f"Average Resolution Time: {filtered_data['Time to Resolve (Minutes)'].mean():.2f} minutes")
            st.write(f"Most Common Downtime Reason: {filtered_data['Downtime Reason'].mode()[0]}")
        
        if not filtered_data.empty:
            downtime_counts = filtered_data["Downtime Reason"].value_counts()
            st.bar_chart(downtime_counts)
        else:
            st.warning("No data available for the selected criteria.")
        downtime_counts = filtered_data["Downtime Reason"].value_counts()
        st.bar_chart(downtime_counts)
    else:
        st.warning("No downtime data found.")
    st.dataframe(st.session_state.data)

### KPI Dashboard ###
with tab2:
    st.header("📊 KPI Dashboard")
    kpi_data = load_from_google_sheets("Project Management", "KPI Dashboard")
    if not kpi_data.empty:
        st.dataframe(kpi_data)
        st.line_chart(kpi_data.set_index("Date"))
    else:
        st.warning("No KPI data found.")

### Personal Productivity ###
with tab3:
    st.header("🎯 Personal Productivity Tracker")
    
    st.subheader("📋 Open and Closed Goals")
    productivity_data = load_from_google_sheets("Project Management", "Personal Productivity")
    if not productivity_data.empty:
        status_filter = st.radio("Show:", ["Open Goals", "Closed Goals", "All"], index=0)
        if status_filter == "Open Goals":
        if "Status" in productivity_data.columns:
            filtered_goals = productivity_data[productivity_data["Status"] != "Closed"]
        else:
            st.warning("No 'Status' column found in the data.")
            filtered_goals = pd.DataFrame()
        if "Status" in productivity_data.columns:
            filtered_goals = productivity_data[productivity_data["Status"] != "Closed"]
        else:
            st.warning("No 'Status' column found in the data.")
            filtered_goals = productivity_data
        if "Status" in productivity_data.columns:
            filtered_goals = productivity_data[productivity_data["Status"] != "Closed"]
        else:
            st.warning("No 'Status' column found in the data.")
            filtered_goals = productivity_data
        if "Status" in productivity_data.columns:
            if "Status" in productivity_data.columns:
                        filtered_goals = productivity_data[productivity_data["Status"] != "Closed"]
        else:
            st.warning("No 'Status' column found in the data.")
            filtered_goals = productivity_data
            elif status_filter == "Closed Goals":
        if "Status" in productivity_data.columns:
            filtered_goals = productivity_data[productivity_data["Status"] == "Closed"]
        else:
            st.warning("No 'Status' column found in the data.")
            filtered_goals = pd.DataFrame()
        if "Status" in productivity_data.columns:
            filtered_goals = productivity_data[productivity_data["Status"] == "Closed"]
        else:
            st.warning("No 'Status' column found in the data.")
            filtered_goals = productivity_data
        if "Status" in productivity_data.columns:
            filtered_goals = productivity_data[productivity_data["Status"] == "Closed"]
        else:
            st.warning("No 'Status' column found in the data.")
            filtered_goals = productivity_data
        if "Status" in productivity_data.columns:
            if "Status" in productivity_data.columns:
                        filtered_goals = productivity_data[productivity_data["Status"] == "Closed"]
        else:
            st.warning("No 'Status' column found in the data.")
            filtered_goals = productivity_data
        else:
        filtered_goals = productivity_data
        
        st.dataframe(filtered_goals)
    else:
        st.warning("No goals found.")
    with st.form("goal_setting_form", clear_on_submit=True):
        goal_name = st.text_input("Goal Name")
        goal_priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        goal_due_date = st.date_input("Due Date")
        add_goal_btn = st.form_submit_button("Add Goal")
        if add_goal_btn:
            new_goal = pd.DataFrame([[goal_name, goal_priority, goal_due_date, "Open"]], columns=["Goal Name", "Priority", "Due Date", "Status"])
            new_goal = new_goal.astype(str)
            append_to_google_sheets(new_goal, "Project Management", "Personal Productivity")
            st.success("Goal added successfully!")
    
    # Voice Note Entry
    recognizer = sr.Recognizer()
    with st.expander("🎙️ Voice Note Entry"):
        if st.button("Record Voice Note"):
            with sr.Microphone() as source:
                st.info("Listening...")
                try:
                    audio = recognizer.listen(source, timeout=5)
                    text = recognizer.recognize_google(audio)
                    st.write("Transcribed Text:", text)
                    new_note = pd.DataFrame([[text]], columns=["Voice Note"])
                    new_note = new_note.astype(str)
                    append_to_google_sheets(new_note, "Project Management", "Personal Productivity")
                except sr.UnknownValueError:
                    st.error("Could not understand audio.")
                except sr.RequestError:
                    st.error("Speech Recognition service unavailable.")

st.success("App updated with Personal Productivity linked to Google Sheets!")
