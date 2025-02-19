import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import pytz  # Timezone handling
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

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Time", "Process Name", "Downtime Reason", "Action Taken", "Root Cause", "Time to Resolve (Minutes)", "Resolved (Y/N)", "Status"])

# App title
st.title("Operations Management Assistant")

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

st.sidebar.subheader("💡 Motivational Quote")
st.sidebar.write(get_motivational_quote())

# Create tabs
tab1, tab2, tab3, tab4 = st.tabs(["Downtime Issues", "KPI Dashboard", "Personal Productivity", "Task Delegation"]) 

downtime_data = load_from_google_sheets("Project Management", "Downtime Issues")

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
    st.subheader("📝 Update Downtime Status")
    if not downtime_data.empty and "Key" in downtime_data.columns:
        downtime_options = downtime_data["Key"].dropna().tolist()
    else:
        st.warning("No 'Key' column found in the data.")
        downtime_options = []
    
    if downtime_options:
        selected_downtime = st.selectbox("Select Downtime Issue to Update (by Key)", downtime_options)
        new_status = st.selectbox("Update Status", ["Open", "In Progress", "Resolved"])
        update_downtime_btn = st.button("Update Downtime Status")
        if update_downtime_btn:
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Downtime Issues")
            data = worksheet.get_all_records()
            for i, row in enumerate(data, start=2):
                if row["Key"] == selected_downtime:
                    status_col_index = worksheet.find("Status").col
                    worksheet.update_cell(i, status_col_index, new_status)
                    st.success(f"Status updated for '{selected_downtime}' to '{new_status}'!")
                    break
    
    st.subheader("📈 Downtime Trends")
    start_date = st.date_input("Start Date", value=date.today())
    end_date = st.date_input("End Date", value=date.today())
    
    if not downtime_data.empty:
        downtime_data["Date"] = pd.to_datetime(downtime_data["Date"])
        filtered_data = downtime_data[(downtime_data["Date"] >= pd.to_datetime(start_date)) & (downtime_data["Date"] <= pd.to_datetime(end_date))]
        st.dataframe(filtered_data)
        
        st.subheader("📊 Daily Downtime Line Chart")
        daily_downtime = filtered_data.groupby(filtered_data["Date"].dt.date).size()
        st.line_chart(daily_downtime)
        
        st.subheader("📊 Pareto Chart for Downtime Reasons")
        downtime_counts = filtered_data["Downtime Reason"].value_counts()
        downtime_counts = downtime_counts.sort_values(ascending=False)
        st.bar_chart(downtime_counts)
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

### Task Delegation ###
with tab4:
    st.header("📌 Task Delegation")
    task_data = load_from_google_sheets("Project Management", "Task Delegation")
    
    if not task_data.empty:
        st.subheader("📝 Update Task Status")
        if "Task Name" in task_data.columns:
            task_options = task_data["Task Name"].dropna().tolist()
        else:
            st.warning("No 'Task Name' column found in the data.")
            task_options = []
        
        if task_options:
            selected_task = st.selectbox("Select Task to Update", task_options)
            new_status = st.selectbox("Update Status", ["Not Started", "In Progress", "Completed"])
            update_task_btn = st.button("Update Task Status")
            
            if update_task_btn:
                spreadsheet = client.open("Project Management")
                worksheet = spreadsheet.worksheet("Task Delegation")
                data = worksheet.get_all_records()
                for i, row in enumerate(data, start=2):
                    if row["Task Name"] == selected_task:
                        status_col_index = worksheet.find("Status").col
                        worksheet.update_cell(i, status_col_index, new_status)
                        st.success(f"Status updated for '{selected_task}' to '{new_status}'!")
                        break
    
    st.subheader("📋 Task List for Selected Timeframe")
    start_date = st.date_input("Start Date", value=date.today())
    end_date = st.date_input("End Date", value=date.today())
    
    if not task_data.empty:
        task_data["Due Date"] = pd.to_datetime(task_data["Due Date"])
        filtered_tasks = task_data[(task_data["Due Date"] >= pd.to_datetime(start_date)) & (task_data["Due Date"] <= pd.to_datetime(end_date))]
        st.dataframe(filtered_tasks)
    else:
        st.warning("No task data available.")
    
    st.subheader("📝 Update Task Status by Key")
    if "Key" in task_data.columns:
        task_keys = task_data["Key"].dropna().tolist()
    else:
        st.warning("No 'Key' column found in the data.")
        task_keys = []
    
    if task_keys:
        selected_task_key = st.selectbox("Select Task to Update (by Key)", task_keys)
        new_status = st.selectbox("Update Status", ["Not Started", "In Progress", "Completed"])
        update_task_by_key_btn = st.button("Update Task Status by Key")
        
        if update_task_by_key_btn:
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Task Delegation")
            data = worksheet.get_all_records()
            for i, row in enumerate(data, start=2):
                if row["Key"] == selected_task_key:
                    status_col_index = worksheet.find("Status").col
                    worksheet.update_cell(i, status_col_index, new_status)
                    st.success(f"Status updated for Task Key '{selected_task_key}' to '{new_status}'!")
                    break
    
st.subheader("📋 Tasks")
st.dataframe(task_data)
    
    with st.form("task_assignment_form", clear_on_submit=True):
        task_name = st.text_input("Task Name")
        assignee = st.text_input("Assigned To")
        due_date = st.date_input("Due Date")
        priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        add_task_btn = st.form_submit_button("Assign Task")
        
        if add_task_btn:
            new_task = pd.DataFrame([[task_name, assignee, due_date, priority, "Not Started"]], columns=["Task Name", "Assigned To", "Due Date", "Priority", "Status"])
            new_task = new_task.astype(str)
            append_to_google_sheets(new_task, "Project Management", "Task Delegation")
            st.success("Task assigned successfully!")

### Personal Productivity ###
with tab3:
    st.header("🎯 Personal Productivity Tracker")
    
    productivity_data = load_from_google_sheets("Project Management", "Personal Productivity")
    if not productivity_data.empty:
        st.subheader("📝 Update Goal Status")
        if "Goal Name" in productivity_data.columns:
            goal_options = productivity_data["Goal Name"].dropna().tolist()
        else:
            st.warning("No 'Goal Name' column found in the data.")
            goal_options = []
        if goal_options:
            selected_goal = st.selectbox("Select Goal to Update", goal_options)
            new_status = st.selectbox("Update Status", ["Open", "In Progress", "Completed"])
            update_status_btn = st.button("Update Status")
            if update_status_btn:
                spreadsheet = client.open("Project Management")
                worksheet = spreadsheet.worksheet("Personal Productivity")
                data = worksheet.get_all_records()
                for i, row in enumerate(data, start=2):  # Google Sheets index starts at 2 because headers are in row 1
                    if row["Goal Name"] == selected_goal:
                        status_col_index = worksheet.find("Status").col  # Locate the "Status" column
                        worksheet.update_cell(i, status_col_index, new_status)
                        st.success(f"Status updated for '{selected_goal}' to '{new_status}'!")
                        break
    
    st.subheader("📋 Goals")
    st.dataframe(productivity_data)

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
