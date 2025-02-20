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

    # Add New Downtime Issue
    st.subheader("Add New Downtime Issue")
    with st.form("new_downtime_issue", clear_on_submit=True):
        date_reported = st.date_input("Date", value=date.today())
        process_name = st.text_input("Process Name")
        downtime_reason = st.text_input("Downtime Reason")
        action_taken = st.text_input("Action Taken")
        root_cause = st.text_input("Root Cause")
        time_to_resolve = st.number_input("Time to Resolve (Minutes)", min_value=1, step=1)
        status = st.selectbox("Status", ["Open", "In Progress", "Closed"])
        submitted = st.form_submit_button("Add Downtime Issue")
        if submitted:
            new_data = pd.DataFrame([[date_reported, process_name, downtime_reason, action_taken, root_cause, time_to_resolve, status]],
                                    columns=["Date", "Process Name", "Downtime Reason", "Action Taken", "Root Cause", "Time to Resolve (Minutes)", "Status"])
            append_to_google_sheets(new_data, "Project Management", "Downtime Issues")

    # Update Downtime Issue
    st.subheader("Update Downtime Issue")
    if not downtime_data.empty and "Key" in downtime_data.columns:
        issue_keys = downtime_data["Key"].dropna().tolist()
        selected_key = st.selectbox("Select Issue to Update", issue_keys)
        new_status = st.selectbox("Update Status", ["Open", "In Progress", "Closed"])
        update_btn = st.button("Update Issue")
        if update_btn:
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Downtime Issues")
            data = worksheet.get_all_records()
            for i, row in enumerate(data, start=2):
                if row["Key"] == selected_key:
                    status_col_index = worksheet.find("Status").col
                    worksheet.update_cell(i, status_col_index, new_status)
                    st.success(f"Status updated for issue '{selected_key}'!")
                    break

    # Display Table View
    st.subheader("Downtime Data Table")
    if not downtime_data.empty:
        st.dataframe(downtime_data)

    # Pareto Analysis
    st.subheader("Pareto Analysis")
    start_date = st.date_input("Start Date", value=date.today())
    end_date = st.date_input("End Date", value=date.today())
    filtered_data = downtime_data[(pd.to_datetime(downtime_data["Date"]) >= pd.to_datetime(start_date)) & (pd.to_datetime(downtime_data["Date"]) <= pd.to_datetime(end_date))]
    if not filtered_data.empty:
        pareto_data = filtered_data["Downtime Reason"].value_counts().sort_values(ascending=False)
        st.bar_chart(pareto_data)

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
    if not productivity_data.empty:
        st.dataframe(productivity_data)

### Task Delegation ###
with tab4:
    st.header("📌 Task Delegation")
    task_data = load_from_google_sheets("Project Management", "Task Delegation")
    if not task_data.empty:
        st.dataframe(task_data)
