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
def append_to_google_sheets(data, sheet_name="Project Management"):
    try:
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.sheet1  # Use the first sheet
        data_as_list = data.values.tolist()
        worksheet.append_rows(data_as_list, table_range="A1")
        st.success("Data appended to Google Sheets!")
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' not found. Ensure it exists and is shared with the service account.")

# Load data from Google Sheets
def load_from_google_sheets(sheet_name="Project Management"):
    try:
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.sheet1  # Use the first sheet
        data = pd.DataFrame(worksheet.get_all_records())
        return data
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' not found. Ensure it exists and is shared with the service account.")
        return pd.DataFrame()

# Validate time format
def validate_time_format(time_str):
    try:
        datetime.strptime(time_str, "%H:%M:%S")
        return True
    except ValueError:
        return False

# Fetch tasks from Google Sheets
def get_tasks():
    client = gspread.authorize(credentials)
    sheet = client.open("Project Management").worksheet("Tasks")
    data = sheet.get_all_records()
    return pd.DataFrame(data)

# Add a new task
def add_task(task_name, priority, due_date):
    client = gspread.authorize(credentials)
    sheet = client.open("Project Management").worksheet("Tasks")
    tasks_df = get_tasks()
    new_task_id = len(tasks_df) + 1  # Auto-increment Task ID
    sheet.append_row([new_task_id, task_name, priority, due_date, "Pending"])

# Update task status
def update_task_status(task_id, status):
    client = gspread.authorize(credentials)
    sheet = client.open("Project Management").worksheet("Tasks")
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if row["Task ID"] == task_id:
            sheet.update_cell(i, 5, status)  # Update Status column
            break

# Delete a task
def delete_task(task_id):
    client = gspread.authorize(credentials)
    sheet = client.open("Project Management").worksheet("Tasks")
    data = sheet.get_all_records()
    for i, row in enumerate(data, start=2):
        if row["Task ID"] == task_id:
            sheet.delete_rows(i)
            break

# Task Management UI
def task_dashboard():
    st.title("📌 Task Management Dashboard")
    tasks_df = get_tasks()
    if tasks_df.empty:
        st.warning("No tasks found.")
    else:
        st.dataframe(tasks_df)
    st.sidebar.header("Update Tasks")
    if not tasks_df.empty:
        task_id = st.sidebar.selectbox("Select Task ID", tasks_df["Task ID"])
        new_status = st.sidebar.selectbox("Update Status", ["Pending", "In Progress", "Done"])
        update_task_btn = st.sidebar.button("Update Status")
        if update_task_btn:
            update_task_status(task_id, new_status)
            st.success("Task updated successfully!")
            st.rerun()

    st.sidebar.header("Delete Tasks")
    if not tasks_df.empty:
        delete_task_id = st.sidebar.selectbox("Select Task to Delete", tasks_df["Task ID"])
        delete_task_btn = st.sidebar.button("Delete Task")
        if delete_task_btn:
            delete_task(delete_task_id)
            st.warning("Task deleted!")
            st.rerun()
    
    with st.form("add_task_form"):
        task_name = st.text_input("Task Name")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        due_date = st.date_input("Due Date")
        add_task_btn = st.form_submit_button("Add Task")
        if add_task_btn:
            add_task(task_name, priority, str(due_date))
            st.success("Task added successfully!")
            st.rerun()

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Time", "Process Name", "Downtime Reason", "Action Taken", "Root Cause", "Time to Resolve (Minutes)", "Resolved (Y/N)"])

# App title
st.title("Operations Management Assistant")

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Downtime Issues", "Project Management", "KPI Dashboard", "Personal Productivity"])

### Downtime Tracking ###
with tab1:
    st.header("Enter Downtime Issue")
    # Existing downtime tracking form and logic here

### Task Management ###
with tab2:
    st.header("Task Management Dashboard")
    task_dashboard()

### KPI Dashboard ###
with tab3:
    st.header("📊 KPI Dashboard")
    kpi_data = load_from_google_sheets("KPI Dashboard")
    if not kpi_data.empty:
        st.dataframe(kpi_data)
        st.line_chart(kpi_data.set_index("Date"))
    else:
        st.warning("No KPI data found.")

### Personal Productivity ###
with tab4:
    st.header("🎯 Personal Productivity Tracker")
    # Goal setting and voice note entry implementation here

st.success("App updated with new features!")
