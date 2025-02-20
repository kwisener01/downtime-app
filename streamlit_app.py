import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import pytz
import requests  # For fetching motivational quotes

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
        worksheet = spreadsheet.worksheet(worksheet_name)
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

# Fetch a motivational quote
def get_motivational_quote():
    try:
        response = requests.get("https://api.quotable.io/random")
        if response.status_code == 200:
            quote_data = response.json()
            return f'"{quote_data["content"]}" - {quote_data["author"]}'
        else:
            return "Stay motivated and keep pushing forward!"
    except:
        return "Stay motivated and keep pushing forward!"

# App title
st.title("Operations Management Assistant")

# Display motivational quote
st.sidebar.subheader("💡 Motivational Quote")
st.sidebar.write(get_motivational_quote())

# Initialize tabs
tab1, tab2, tab3, tab4 = st.tabs(["Downtime Issues", "KPI Dashboard", "Personal Productivity", "Task Delegation"])

### Downtime Issues ###
with tab1:
    st.header("🔧 Downtime Issues")

    downtime_data = load_from_google_sheets("Project Management", "Downtime Issues")

    # Ensure required columns exist
    for col in ["Resolution Time", "Process Name", "Downtime Reason", "Root Cause", "Status", "Key"]:
        if col not in downtime_data.columns:
            downtime_data[col] = "Unknown"

    st.subheader("➕ Add Downtime Event")
    with st.form("downtime_form", clear_on_submit=True):
        event_date = st.date_input("Event Date", value=date.today())
        process_name = st.text_input("Process Name")
        downtime_reason = st.text_input("Downtime Reason")
        root_cause = st.text_input("Root Cause")
        resolution_time = st.number_input("Resolution Time (minutes)", min_value=0)
        status = st.selectbox("Status", ["Open", "In Progress", "Closed"])
        key_number = st.text_input("Key Number")
        add_event_btn = st.form_submit_button("Add Event")
        if add_event_btn:
            new_event = pd.DataFrame([[event_date, process_name, downtime_reason, root_cause, resolution_time, status, key_number]], 
                                     columns=["Date", "Process Name", "Downtime Reason", "Root Cause", "Resolution Time", "Status", "Key"])
            new_event = new_event.astype(str)
            append_to_google_sheets(new_event, "Project Management", "Downtime Issues")
            st.success("Downtime event added successfully!")

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
    st.header("🎯 Personal Productivity")
    productivity_data = load_from_google_sheets("Project Management", "Personal Productivity")
    if not productivity_data.empty:
        st.dataframe(productivity_data)
    else:
        st.warning("No personal productivity data found.")

    st.subheader("➕ Add Personal Goal")
    with st.form("goal_form", clear_on_submit=True):
        goal_name = st.text_input("Goal Name")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        due_date = st.date_input("Due Date")
        status = "Open"
        add_goal_btn = st.form_submit_button("Add Goal")
        if add_goal_btn:
            new_goal = pd.DataFrame([[goal_name, priority, due_date, status]], 
                                    columns=["Goal Name", "Priority", "Due Date", "Status"])
            new_goal = new_goal.astype(str)
            append_to_google_sheets(new_goal, "Project Management", "Personal Productivity")
            st.success("Goal added successfully!")

### Task Delegation ###
with tab4:
    st.header("📋 Task Delegation")
    task_data = load_from_google_sheets("Project Management", "Task Delegation")
    if not task_data.empty:
        st.dataframe(task_data)
    else:
        st.warning("No task delegation data found.")

    st.subheader("➕ Assign New Task")
    with st.form("task_form", clear_on_submit=True):
        task_name = st.text_input("Task Name")
        assigned_to = st.text_input("Assigned To")
        due_date = st.date_input("Due Date")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        status = "Not Started"
        add_task_btn = st.form_submit_button("Assign Task")
        if add_task_btn:
            new_task = pd.DataFrame([[task_name, assigned_to, due_date, priority, status]], 
                                     columns=["Task Name", "Assigned To", "Due Date", "Priority", "Status"])
            new_task = new_task.astype(str)
            append_to_google_sheets(new_task, "Project Management", "Task Delegation")
            st.success("Task assigned successfully!")
