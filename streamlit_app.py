import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import pytz  # Timezone handling
import matplotlib.pyplot as plt

# Define the scope
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']

# Load credentials from Streamlit Secrets
credentials = Credentials.from_service_account_info(st.secrets["google_sheets"], scopes=scope)

# Authorize gspread
client = gspread.authorize(credentials)

# Set timezone to EST (Eastern Standard Time)
est = pytz.timezone("US/Eastern")

# Append data to Google Sheets
def append_to_google_sheets(data, sheet_name, worksheet_name):
    try:
        spreadsheet = client.open(sheet_name)
        worksheet = spreadsheet.worksheet(worksheet_name)
        data_as_list = data.values.tolist()
        worksheet.append_rows(data_as_list, table_range="A1")
        st.success(f"Data appended to Google Sheets: {worksheet_name}")
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

# App title
st.title("Operations Management Assistant")

# Create tabs
tab1, tab2, tab3 = st.tabs(["Downtime Issues", "KPI Dashboard", "Personal Productivity"])

# Load Data
downtime_data = load_from_google_sheets("Project Management", "Downtime Issues")
productivity_data = load_from_google_sheets("Project Management", "Personal Productivity")

##################################################################################################################
### Downtime Issues ###
##################################################################################################################
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

        # Auto-close if resolved
        status = "Closed" if resolved == "Y" else "Open"
        resolution_time = datetime.now(est) + pd.Timedelta(minutes=time_to_resolve) if resolved == "Y" else ""

        submitted = st.form_submit_button("Add Data")

        if submitted:
            key = len(downtime_data) + 1
            new_row = pd.DataFrame([{
                "Key": key, 
                "Date": today_date.strftime("%Y-%m-%d"), 
                "Time": defect_time, 
                "Process Name": process_name, 
                "Downtime Reason": downtime_reason, 
                "Action Taken": action_taken, 
                "Root Cause": root_cause, 
                "Time to Resolve (Minutes)": time_to_resolve, 
                "Resolved (Y/N)": resolved,
                "Status": status,
                "Resolution Time": resolution_time
            }])

            downtime_data = pd.concat([downtime_data, new_row], ignore_index=True)
            append_to_google_sheets(new_row, "Project Management", "Downtime Issues")

    # Filters
    show_open_only = st.checkbox("Show Only Open Issues", value=False)
    start_date = st.date_input("Start Date", value=date.today())
    end_date = st.date_input("End Date", value=date.today())

    # Apply filters
    filtered_downtime = downtime_data.copy()
    if show_open_only:
        filtered_downtime = filtered_downtime[filtered_downtime["Status"] != "Closed"]

    filtered_downtime["Date"] = pd.to_datetime(filtered_downtime["Date"], errors='coerce')
    filtered_downtime = filtered_downtime[
        (filtered_downtime["Date"] >= pd.to_datetime(start_date)) & 
        (filtered_downtime["Date"] <= pd.to_datetime(end_date))
    ]
    st.dataframe(filtered_downtime)

    # 📊 Pareto Chart
    st.subheader("Pareto Chart of Downtime Reasons")
    if not filtered_downtime.empty:
        pareto_data = filtered_downtime.groupby("Downtime Reason")["Time to Resolve (Minutes)"].sum().sort_values(ascending=False)
        cumulative_percentage = pareto_data.cumsum() / pareto_data.sum() * 100

        fig, ax1 = plt.subplots(figsize=(10, 5))
        ax1.bar(pareto_data.index, pareto_data.values, color="blue", alpha=0.6)
        ax2 = ax1.twinx()
        ax2.plot(pareto_data.index, cumulative_percentage, color="red", marker="o")
        ax2.set_ylim(0, 110)
        ax1.set_title("Pareto Chart of Downtime Reasons")
        fig.tight_layout()
        st.pyplot(fig)

##################################################################################################################
### KPI Dashboard ###
##################################################################################################################
with tab2:
    st.header("📊 KPI Dashboard")
    kpi_data = load_from_google_sheets("Project Management", "KPI Dashboard")
    st.dataframe(kpi_data)

##################################################################################################################
### Personal Productivity ###
##################################################################################################################
with tab3:
    st.header("🎯 Personal Productivity Tracker")

    st.subheader("Update Task, Responsible Person & Notes")
    if not productivity_data.empty:
        task_options = [f"{row['Key']} - {row['Task Name']}" for _, row in productivity_data.iterrows()]
        selected_task = st.selectbox("Select Task to Update", task_options)
        selected_key = int(selected_task.split(" - ")[0])
        task_row = productivity_data[productivity_data["Key"] == selected_key].iloc[0]

        updated_name = st.text_input("Update Task Name", value=task_row["Task Name"])
        updated_priority = st.selectbox("Update Priority", ["Low", "Medium", "High"], index=["Low", "Medium", "High"].index(task_row["Priority"]))
        updated_due_date = st.date_input("Update Due Date", value=pd.to_datetime(task_row["Due Date"]).date())
        updated_status = st.selectbox("Update Status", ["Not Started", "In Progress", "Completed"], index=["Not Started", "In Progress", "Completed"].index(task_row["Status"]))
        updated_responsible = st.text_input("Assign Responsible Person", value=task_row.get("Responsible", ""))
        updated_notes = st.text_area("Add or Update Notes", value=task_row.get("Notes", ""))

        if st.button("Update Task Details"):
            append_to_google_sheets(pd.DataFrame([task_row]), "Project Management", "Personal Productivity")
            st.success(f"Task '{updated_name}' updated successfully!")
