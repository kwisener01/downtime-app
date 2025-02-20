import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import pytz
import requests

# Define the scope
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Load credentials from Streamlit Secrets
credentials = Credentials.from_service_account_info(st.secrets["google_sheets"], scopes=scope)

# Authorize gspread
client = gspread.authorize(credentials)

# Set timezone to EST
est = pytz.timezone("US/Eastern")

# Append data to Google Sheets
def append_to_google_sheets(data, sheet_name, worksheet_name):
    try:
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        data_as_list = data.values.tolist()
        worksheet.append_rows(data_as_list, table_range="A1")
        st.success("Data appended to Google Sheets!")
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' not found. Ensure it exists and is shared with the service account.")

# Load data from Google Sheets
def load_from_google_sheets(sheet_name, worksheet_name):
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

# Fetch motivational quote
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

# Sidebar quote
st.sidebar.subheader("💡 Motivational Quote")
st.sidebar.write(get_motivational_quote())

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["Downtime Issues", "KPI Dashboard", "Personal Productivity", "Task Delegation"])

### Downtime Issues ###
with tab1:
    st.header("🔧 Downtime Issues")
    downtime_data = load_from_google_sheets("Project Management", "Downtime Issues")
    
    # Update Status
    if not downtime_data.empty:
        st.subheader("Update Downtime Status")
        key_list = downtime_data["Key"].dropna().tolist()
        selected_key = st.selectbox("Select Key to Update", key_list)
        new_status = st.selectbox("New Status", ["Open", "In Progress", "Closed"])
        if st.button("Update Status"):
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Downtime Issues")
            for i, row in downtime_data.iterrows():
                if row["Key"] == selected_key:
                    worksheet.update_cell(i+2, downtime_data.columns.get_loc("Status") + 1, new_status)
                    st.success(f"Status for Key {selected_key} updated to {new_status}")
                    break

    # Pareto Analysis
    st.subheader("Pareto Analysis")
    start_date = st.date_input("Start Date", value=date.today())
    end_date = st.date_input("End Date", value=date.today())
    filtered_data = downtime_data[(pd.to_datetime(downtime_data["Date"]) >= pd.to_datetime(start_date)) & (pd.to_datetime(downtime_data["Date"]) <= pd.to_datetime(end_date))]
    if not filtered_data.empty:
        pareto_data = filtered_data["Downtime Reason"].value_counts().sort_values(ascending=False)
        st.bar_chart(pareto_data)

        selected_reason = st.selectbox("Select Downtime Reason for Root Cause Pareto", pareto_data.index.tolist())
        root_cause_data = filtered_data[filtered_data["Downtime Reason"] == selected_reason]["Root Cause"].value_counts().sort_values(ascending=False)
        st.bar_chart(root_cause_data)

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
        st.subheader("Update Goal Status")
        goal_list = productivity_data["Goal Name"].dropna().tolist()
        selected_goal = st.selectbox("Select Goal to Update", goal_list)
        new_status = st.selectbox("New Status", ["Open", "In Progress", "Completed"])
        if st.button("Update Goal Status"):
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Personal Productivity")
            for i, row in productivity_data.iterrows():
                if row["Goal Name"] == selected_goal:
                    worksheet.update_cell(i+2, productivity_data.columns.get_loc("Status") + 1, new_status)
                    st.success(f"Status for Goal '{selected_goal}' updated to {new_status}")
                    break

### Task Delegation ###
with tab4:
    st.header("📋 Task Delegation")
    task_data = load_from_google_sheets("Project Management", "Task Delegation")
    if not task_data.empty:
        st.dataframe(task_data)
        st.subheader("Update Task Status")
        task_list = task_data["Task Name"].dropna().tolist()
        selected_task = st.selectbox("Select Task to Update", task_list)
        new_status = st.selectbox("New Status", ["Not Started", "In Progress", "Completed"])
        if st.button("Update Task Status"):
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Task Delegation")
            for i, row in task_data.iterrows():
                if row["Task Name"] == selected_task:
                    worksheet.update_cell(i+2, task_data.columns.get_loc("Status") + 1, new_status)
                    st.success(f"Status for Task '{selected_task}' updated to {new_status}")
                    break
