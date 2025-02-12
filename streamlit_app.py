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
def append_to_google_sheets(data, sheet_name="Downtime Data"):
    try:
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.sheet1  # Use the first sheet

        # Convert DataFrame to list of lists
        data_as_list = data.values.tolist()

        # Append the new data
        worksheet.append_rows(data_as_list, table_range="A1")
        st.success("Data appended to Google Sheets!")
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"Spreadsheet '{sheet_name}' not found. Ensure it exists and is shared with the service account.")

# Load data from Google Sheets
def load_from_google_sheets(sheet_name="Downtime Data"):
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

# Initialize session state
if "data" not in st.session_state:
    st.session_state.data = pd.DataFrame(columns=["Date", "Time", "Process Name", "Downtime Reason", "Action Taken", "Root Cause", "Time to Resolve (Minutes)", "Resolved (Y/N)"])

# App title
st.title("Downtime Issues")

# Manual Data Entry Tab
st.header("Enter Downtime Issue Manually")
with st.form("data_entry_form", clear_on_submit=True):
    today_date = st.date_input("Date", value=date.today())

    # Get current time in EST
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
        # Validate the time format
        if not validate_time_format(defect_time):
            st.error("Invalid time format. Please use HH:MM:SS.")
        else:
            new_row = {
                "Date": today_date.strftime("%Y-%m-%d"),
                "Time": defect_time,
                "Process Name": process_name,
                "Downtime Reason": downtime_reason,
                "Action Taken": action_taken,
                "Root Cause": root_cause,
                "Time to Resolve (Minutes)": time_to_resolve,
                "Resolved (Y/N)": resolved,
            }
            st.session_state.data = pd.concat([st.session_state.data, pd.DataFrame([new_row])], ignore_index=True)
            st.success("Data added successfully!")

            # **Automatically append data to Google Sheets**
            append_to_google_sheets(pd.DataFrame([new_row]))

# Display current data
st.subheader("Current Data")
st.dataframe(st.session_state.data)

# Select date for trend analysis
st.subheader("Review Downtime Trends")
selected_date = st.date_input("Select Date for Analysis", value=date.today())

# Display current data from Google Sheets for the selected date
sheet_data = load_from_google_sheets()
if not sheet_data.empty:
    filtered_data = sheet_data[sheet_data["Date"] == selected_date.strftime("%Y-%m-%d")]

    st.subheader(f"Downtime Data for {selected_date.strftime('%Y-%m-%d')}")
    st.dataframe(filtered_data)

    if not filtered_data.empty:
        st.subheader("Defect Type Trends")
        defect_counts = filtered_data.groupby("Downtime Reason").size()
        st.bar_chart(defect_counts)

        st.subheader("Process Name Trends")
        process_counts = filtered_data.groupby("Process Name").size()
        st.bar_chart(process_counts)

        st.subheader("Root Cause Trends")
        root_cause_counts = filtered_data.groupby("Root Cause").size()
        st.bar_chart(root_cause_counts)
    else:
        st.warning(f"No downtime data available for {selected_date.strftime('%Y-%m-%d')}.")
