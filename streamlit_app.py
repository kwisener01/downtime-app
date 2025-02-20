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
    for col in ["Resolution Time", "Process Name", "Issue", "Status", "Key"]:
        if col not in downtime_data.columns:
            downtime_data[col] = "Unknown"

    st.subheader("➕ Add Downtime Event")
    with st.form("downtime_form", clear_on_submit=True):
        event_date = st.date_input("Event Date", value=date.today())
        process_name = st.text_input("Process Name")
        issue = st.text_input("Issue Description")
        resolution_time = st.number_input("Resolution Time (minutes)", min_value=0)
        status = st.selectbox("Status", ["Open", "In Progress", "Closed"])
        key_number = st.text_input("Key Number")
        add_event_btn = st.form_submit_button("Add Event")
        if add_event_btn:
            new_event = pd.DataFrame([[event_date, process_name, issue, resolution_time, status, key_number]], 
                                     columns=["Date", "Process Name", "Issue", "Resolution Time", "Status", "Key"])
            new_event = new_event.astype(str)
            append_to_google_sheets(new_event, "Project Management", "Downtime Issues")
            st.success("Downtime event added successfully!")

    st.subheader("📝 Update Downtime Status")
    if not downtime_data.empty:
        key_options = downtime_data["Key"].dropna().tolist()
        selected_key = st.selectbox("Select Downtime Issue to Update (by Key)", key_options)
        new_status = st.selectbox("Update Status", ["Open", "In Progress", "Resolved"])
        update_downtime_btn = st.button("Update Downtime Status")
        if update_downtime_btn:
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Downtime Issues")
            data = worksheet.get_all_records()
            for i, row in enumerate(data, start=2):
                if row["Key"] == selected_key:
                    status_col_index = worksheet.find("Status").col
                    worksheet.update_cell(i, status_col_index, new_status)
                    st.success(f"Status updated for Key '{selected_key}' to '{new_status}'!")
                    break

    st.subheader("📈 Downtime Trends")
    start_date = st.date_input("Start Date", value=date.today())
    end_date = st.date_input("End Date", value=date.today())

    if not downtime_data.empty:
        downtime_data["Date"] = pd.to_datetime(downtime_data["Date"], errors='coerce')
        filtered_data = downtime_data[(downtime_data["Date"] >= pd.to_datetime(start_date)) & (downtime_data["Date"] <= pd.to_datetime(end_date))]
        st.dataframe(filtered_data)
        
        st.subheader("📊 Pareto Chart of Issues")
        issue_counts = filtered_data["Issue"].value_counts().sort_values(ascending=False)
        st.bar_chart(issue_counts)
    else:
        st.warning("No downtime data found.")
