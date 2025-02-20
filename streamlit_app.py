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
        data_as_list = data.astype(str).values.tolist()
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

    # Display Table
    st.subheader("Downtime Issues Table")
    st.dataframe(downtime_data)

    # Date Range Filter
    st.subheader("Filter Downtime by Date Range")
    start_date = st.date_input("Start Date", value=date.today())
    end_date = st.date_input("End Date", value=date.today())

    if not downtime_data.empty:
        downtime_data["Date"] = pd.to_datetime(downtime_data["Date"], errors='coerce')
        filtered_data = downtime_data[(downtime_data["Date"] >= pd.to_datetime(start_date)) & (downtime_data["Date"] <= pd.to_datetime(end_date))]
        filtered_data = filtered_data.dropna(subset=["Date"])
        st.dataframe(filtered_data)

    # Pareto Chart
    st.subheader("Pareto Chart of Downtime Reasons")
    if not filtered_data.empty and "Downtime Reason" in filtered_data.columns:
        reason_counts = filtered_data["Downtime Reason"].value_counts().sort_values(ascending=False)
        st.bar_chart(reason_counts)

    # Update Downtime Status
    st.subheader("Update Downtime Status")
    if not downtime_data.empty and "Key" in downtime_data.columns:
        selected_downtime = st.selectbox("Select Downtime Issue to Update (by Key)", downtime_data["Key"].astype(str).tolist(), key="downtime_selectbox")
        new_status = st.selectbox("Update Status", ["Open", "In Progress", "Closed"], key="downtime_status_selectbox")
        if st.button("Update Downtime Status"):
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Downtime Issues")
            cell = worksheet.find(selected_downtime)
            worksheet.update_cell(cell.row, worksheet.find("Status").col, new_status)
            st.success(f"Status updated for Downtime Issue '{selected_downtime}' to '{new_status}'!")

### KPI Dashboard ###
with tab2:
    st.header("📊 KPI Dashboard")
    kpi_data = load_from_google_sheets("Project Management", "KPI Dashboard")
    if not kpi_data.empty:
        st.dataframe(kpi_data)
        st.line_chart(kpi_data.set_index("Date"))

### Personal Productivity ###
with tab3:
    st.header("🎯 Personal Productivity Tracker")
    productivity_data = load_from_google_sheets("Project Management", "Personal Productivity")

    # Display Table
    st.subheader("Productivity Tasks Table")
    st.dataframe(productivity_data)

    # Update Task Status
    st.subheader("Update Task Status")
    if not productivity_data.empty and "Task Name" in productivity_data.columns:
        selected_task = st.selectbox("Select Task to Update", productivity_data["Task Name"].dropna().tolist(), key="productivity_task_selectbox")
        new_status = st.selectbox("Update Status", ["Not Started", "In Progress", "Completed"], key="productivity_status_selectbox")
        if st.button("Update Task Status"):
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Personal Productivity")
            cell = worksheet.find(selected_task)
            worksheet.update_cell(cell.row, worksheet.find("Status").col, new_status)
            st.success(f"Status updated for Task '{selected_task}' to '{new_status}'!")

### Task Delegation ###
with tab4:
    st.header("📌 Task Delegation")
    task_data = load_from_google_sheets("Project Management", "Task Delegation")

    # Display Table
    st.subheader("Task Delegation Table")
    st.dataframe(task_data)

    # Update Task Status
    st.subheader("Update Task Status")
    if not task_data.empty and "Task Name" in task_data.columns:
        selected_task = st.selectbox("Select Task to Update", task_data["Task Name"].dropna().tolist(), key="delegation_task_selectbox")
        new_status = st.selectbox("Update Status", ["Not Started", "In Progress", "Completed"], key="delegation_status_selectbox")
        if st.button("Update Task Status"):
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Task Delegation")
            cell = worksheet.find(selected_task)
            worksheet.update_cell(cell.row, worksheet.find("Status").col, new_status)
            st.success(f"Status updated for Task '{selected_task}' to '{new_status}'!")
