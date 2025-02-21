import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import pytz  # Timezone handling

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

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Time", "Process Name", "Downtime Reason", "Action Taken", "Root Cause", "Time to Resolve (Minutes)", "Resolved (Y/N)"])

# App title
st.title("Operations Management Assistant")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Downtime Issues", "KPI Dashboard", "Personal Productivity"])

# Load Downtime Data
downtime_data = load_from_google_sheets("Project Management", "Downtime Issues")

### Personal Productivity ###
with tab3:
    st.header("🎯 Personal Productivity Tracker")
    productivity_data = load_from_google_sheets("Project Management", "Personal Productivity")

    st.subheader("Task Statistics")
    total_tasks = len(productivity_data)
    open_tasks = len(productivity_data[productivity_data["Status"] == "Open"])
    completed_tasks = len(productivity_data[productivity_data["Status"] == "Completed"])

    st.write(f"Total Tasks: {total_tasks}")
    st.write(f"Open Tasks: {open_tasks}")
    st.write(f"Completed Tasks: {completed_tasks}")

    st.subheader("AI-Powered Priority Suggestions")
    if not productivity_data.empty:
        productivity_data['Due Date'] = pd.to_datetime(productivity_data['Due Date'], errors='coerce')
        today = pd.to_datetime(date.today())
        productivity_data['Days Until Due'] = (productivity_data['Due Date'] - today).dt.days

        # Priority Score Calculation
        def calculate_priority(row):
            priority_score = 0
            if row['Priority'] == 'High':
                priority_score += 3
            elif row['Priority'] == 'Medium':
                priority_score += 2
            else:
                priority_score += 1

            if row['Days Until Due'] <= 3:
                priority_score += 3
            elif row['Days Until Due'] <= 7:
                priority_score += 2
            elif row['Days Until Due'] <= 14:
                priority_score += 1

            return priority_score

        productivity_data['Priority Score'] = productivity_data.apply(calculate_priority, axis=1)
        sorted_tasks = productivity_data.sort_values(by='Priority Score', ascending=False)

        st.subheader("Recommended Task Priorities")
        st.dataframe(sorted_tasks[['Task Name', 'Priority', 'Due Date', 'Days Until Due', 'Priority Score', 'Status']])

    st.subheader("Add New Task")
    with st.form("goal_setting_form", clear_on_submit=True):
        goal_name = st.text_input("Task Name")
        goal_priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        goal_due_date = st.date_input("Due Date")
        add_goal_btn = st.form_submit_button("Add Task")
        if add_goal_btn:
            new_goal = pd.DataFrame([[goal_name, goal_priority, goal_due_date, "Open", ""]], columns=["Task Name", "Priority", "Due Date", "Status", "Actual Close Date"])
            new_goal = new_goal.astype(str)
            append_to_google_sheets(new_goal, "Project Management", "Personal Productivity")
            st.success("Task added successfully!")

    st.subheader("Productivity Tasks Table")

    show_open_tasks = st.checkbox("Show Only Open Tasks", value=False)
    if show_open_tasks:
        filtered_productivity_data = productivity_data[productivity_data["Status"] == "Open"]
    else:
        filtered_productivity_data = productivity_data

    st.dataframe(filtered_productivity_data)

    st.subheader("Update Task Status")
    if not productivity_data.empty and "Task Name" in productivity_data.columns:
        selected_task = st.selectbox("Select Task to Update", productivity_data["Task Name"].dropna().tolist(), key="productivity_task_selectbox")
        new_status = st.selectbox("Update Status", ["Not Started", "In Progress", "Completed"], key="productivity_status_selectbox")
        if st.button("Update Task Status"):
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Personal Productivity")
            cell = worksheet.find(selected_task)
            worksheet.update_cell(cell.row, worksheet.find("Status").col, new_status)
            if new_status == "Completed":
                current_date = datetime.now(est).strftime("%Y-%m-%d")
                worksheet.update_cell(cell.row, worksheet.find("Actual Close Date").col, current_date)
            st.success(f"Status updated for Task '{selected_task}' to '{new_status}'!")
