import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date
import pytz  # Timezone handling
import uuid  # For generating unique keys
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


##################################################################################################################
##################################################################################################################
### Downtime Tracking ###
##################################################################################################################
with tab1:

# Enter Downtime Issue
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

    
        # Auto-close issue if "Resolved" is Yes
        status = "Closed" if resolved == "Y" else "Open"
        
        # Calculate Resolution Time if closed
        resolution_time = ""
        if resolved == "Y":
            resolution_time = (datetime.now(est) + pd.Timedelta(minutes=time_to_resolve)).strftime("%Y-%m-%d %H:%M:%S")
    
        submitted = st.form_submit_button("Add Data")
    
        if submitted:
            key = len(downtime_data) + 1  # Use index as the key
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
    
            # Use pd.concat() instead of append() to avoid AttributeError
            downtime_data = pd.concat([downtime_data, new_row], ignore_index=True)
            append_to_google_sheets(new_row, "Project Management", "Downtime Issues")
###################################################################################

##################################################################################################################
##################################################################################################################

    # Display Table with Filters
    st.subheader("Downtime Issues Table")
    
    # Checkbox to show only open issues
    show_open_only = st.checkbox("Show Only Open Issues", value=False, key="filter_open_issues")
    
    # Date range filter
    st.subheader("Filter Downtime by Date Range")
    start_date = st.date_input("Start Date", value=date.today(), key="start_date_filter")
    end_date = st.date_input("End Date", value=date.today(), key="end_date_filter")
    
    # Apply filters to downtime data
    filtered_downtime = downtime_data.copy()
    
    # Filter open issues if checkbox is selected
    if show_open_only:
        filtered_downtime = filtered_downtime[filtered_downtime["Status"] != "Closed"]
    
    # Apply date range filter
    filtered_downtime["Date"] = pd.to_datetime(filtered_downtime["Date"], errors='coerce')
    filtered_downtime = filtered_downtime[
        (filtered_downtime["Date"] >= pd.to_datetime(start_date)) & 
        (filtered_downtime["Date"] <= pd.to_datetime(end_date))
    ]
    
    # Display filtered downtime table
    st.dataframe(filtered_downtime)
    ##################################################################################################################
    ##################################################################################################################
    
    # 📊 Downtime Statistics
    st.subheader("📈 Downtime Statistics")
    total_issues = len(filtered_downtime)
    open_issues = len(filtered_downtime[filtered_downtime["Status"] != "Closed"])
    closed_issues = total_issues - open_issues
    avg_resolution_time = filtered_downtime["Time to Resolve (Minutes)"].mean()
    
    st.write(f"**Total Issues:** {total_issues}")
    st.write(f"**Open Issues:** {open_issues}")
    st.write(f"**Closed Issues:** {closed_issues}")
    st.write(f"**Avg Resolution Time:** {avg_resolution_time:.2f} minutes")
    
    
    # Update Downtime Status with Custom Resolution Time
    st.subheader("Update Downtime Status")
    if not downtime_data.empty:
        # Format options as "Key - Process Name"
        downtime_options = [f"{row['Key']} - {row['Process Name']}" for _, row in downtime_data.iterrows()]
        selected_downtime = st.selectbox("Select Downtime Issue to Update (Key - Process Name)", 
                                         downtime_options, key="downtime_selectbox")
    
        new_status = st.selectbox("Update Status", ["Open", "In Progress", "Closed"], key="downtime_status_selectbox")
        
        # Allow user to manually update resolution time
        custom_resolution_time = st.text_input("Custom Resolution Time (YYYY-MM-DD HH:MM:SS)", value="")
    
        if st.button("Update Downtime Status"):
            # Extract Key from the selection
            selected_key = int(selected_downtime.split(" - ")[0])
    
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Downtime Issues")
    
            # Find the row index using the Key
            row_index = selected_key + 1  # Adjust for 1-based index in Google Sheets
    
            worksheet.update_cell(row_index, worksheet.find("Status").col, new_status)
    
            # If status is marked as "Closed", update the resolution time
            if new_status == "Closed":
                resolution_time = custom_resolution_time if custom_resolution_time else datetime.now(est).strftime("%Y-%m-%d %H:%M:%S")
                worksheet.update_cell(row_index, worksheet.find("Resolution Time").col, resolution_time)
            
            st.success(f"Status updated for Downtime Issue '{selected_downtime}' to '{new_status}' with Resolution Time '{resolution_time}'!")
    
    ##################################################################################################################
    ##################################################################################################################
    ##################################################################################################################
    
    
    
    
    
    
    # 📊 Pareto Chart: Sorted by Total Downtime with Cumulative Line
    st.subheader("Pareto Chart of Downtime Reasons (Sorted by Total Downtime)")
    
    if not filtered_downtime.empty and "Downtime Reason" in filtered_downtime.columns:
        # Aggregate downtime per reason and sort from largest to smallest
        pareto_data = (
            filtered_downtime.groupby("Downtime Reason")["Time to Resolve (Minutes)"]
            .sum()
            .sort_values(ascending=False)
        )
    
        # Compute cumulative percentage
        cumulative_percentage = pareto_data.cumsum() / pareto_data.sum() * 100
    
        # Plotting with Matplotlib to ensure proper formatting
        fig, ax1 = plt.subplots(figsize=(10, 5))
    
        # Bar chart (Downtime per Reason)
        ax1.bar(pareto_data.index, pareto_data.values, color="blue", alpha=0.6, label="Total Downtime (Minutes)")
        ax1.set_ylabel("Total Downtime (Minutes)", color="blue")
        ax1.tick_params(axis="y", labelcolor="blue")
        ax1.set_xticklabels(pareto_data.index, rotation=45, ha="right")
    
        # Secondary axis: Cumulative Pareto Line
        ax2 = ax1.twinx()
        ax2.plot(pareto_data.index, cumulative_percentage, color="red", marker="o", linestyle="-", label="Cumulative %")
        ax2.set_ylabel("Cumulative Percentage (%)", color="red")
        ax2.tick_params(axis="y", labelcolor="red")
        ax2.set_ylim(0, 110)
    
        # Title and legend
        ax1.set_title("Pareto Chart of Downtime Reasons")
        fig.tight_layout()
        st.pyplot(fig)
    
    
    # 📉 Downtime Issues & Insights
    st.header("📉 Downtime Issues & Insights")
    
    # Display filtered downtime data
    #st.subheader("Downtime Issues Table")
    #st.dataframe(filtered_downtime)
    
    # 📊  Insights
    st.subheader("💡 Data Insights")
    
    if not filtered_downtime.empty:
        filtered_downtime["Date"] = pd.to_datetime(filtered_downtime["Date"], errors='coerce')
        filtered_downtime["Time to Resolve (Minutes)"] = pd.to_numeric(filtered_downtime["Time to Resolve (Minutes)"], errors='coerce')
    
        # 🚨 Identify Top 3 Frequent Root Causes
        if "Root Cause" in filtered_downtime.columns:
            root_cause_counts = filtered_downtime["Root Cause"].value_counts()
            top_root_causes = root_cause_counts.head(3)
    
            st.markdown("### 🔥 **Top 3 Root Causes**")
            for cause, count in top_root_causes.items():
                st.write(f"- **{cause}**: {count} occurrences")
    
        # ⚠️ Flag High-Resolution Time Issues
        high_res_time_issues = filtered_downtime[filtered_downtime["Time to Resolve (Minutes)"] > filtered_downtime["Time to Resolve (Minutes)"].mean()]
        
        if not high_res_time_issues.empty:
            st.markdown("### ⏳ **High-Resolution Time Downtime Issues**")
            st.dataframe(high_res_time_issues[["Key", "Process Name", "Downtime Reason", "Time to Resolve (Minutes)"]])
    
        # 📈 Trend Analysis for Recurring Issues
        downtime_trend = filtered_downtime.groupby(filtered_downtime["Date"].dt.to_period("M"))["Time to Resolve (Minutes)"].sum()
        downtime_trend.index = downtime_trend.index.to_timestamp()
        
        st.subheader("📈 Downtime Trend Analysis")
        st.line_chart(downtime_trend)
    
    # 🔍 Suggestions
    st.subheader("🚀 Suggestions for Improvement")
    
    if not filtered_downtime.empty:
        st.markdown("### 🛠 **Actionable Recommendations**")
    
        # 🛑 Preventive Maintenance for Top Causes
        if not top_root_causes.empty:
            for cause in top_root_causes.index:
                st.write(f"- **Implement a Preventive Maintenance Plan for:** {cause}")
    
        # ⚙️ Training & SOP Adjustments
        if len(top_root_causes) > 1:
            st.write("- **Review standard operating procedures (SOPs)** for recurring downtime issues.")
            st.write("- **Provide additional training** for operators on handling the most common issues.")
    
        # ⏱ Reducing High-Resolution Time
        if not high_res_time_issues.empty:
            st.write("- **Investigate downtime issues with unusually high resolution times** and optimize response strategies.")
    
        # ⚡ Urgent Action Alert
        if filtered_downtime["Time to Resolve (Minutes)"].mean() > 30:
            st.warning("⚠️ High average resolution time detected! Consider faster troubleshooting processes.")
    
    
    
    ######################################################################################3
    
    ##################################################################################################################
    ##################################################################################################################
    ##################################################################################################################

### KPI Dashboard ###
with tab2:
    st.header("📊 KPI Dashboard")
    kpi_data = load_from_google_sheets("Project Management", "KPI Dashboard")
    if not kpi_data.empty:
        st.dataframe(kpi_data)
        st.line_chart(kpi_data.set_index("Date"))

    # Dynamic KPI Calculations
    if not downtime_data.empty:
        downtime_data["Time to Resolve (Minutes)"] = pd.to_numeric(downtime_data["Time to Resolve (Minutes)"], errors='coerce')
        total_downtime = downtime_data["Time to Resolve (Minutes)"].sum()
        avg_downtime = downtime_data["Time to Resolve (Minutes)"].mean()
        st.subheader("Dynamic KPIs")
        st.write(f"Total Downtime: {total_downtime} minutes")
        st.write(f"Average Downtime: {avg_downtime:.2f} minutes")

        # Trend Analysis - Downtime Over Time
        downtime_data["Date"] = pd.to_datetime(downtime_data["Date"], errors='coerce')
        downtime_trend = downtime_data.groupby(downtime_data["Date"].dt.to_period("M"))["Time to Resolve (Minutes)"].sum()
        downtime_trend.index = downtime_trend.index.to_timestamp()
        st.subheader("Downtime Trend Analysis")
        st.line_chart(downtime_trend)


### Personal Productivity ###
with tab3:
    st.header("🎯 Personal Productivity Tracker")
    productivity_data = load_from_google_sheets("Project Management", "Personal Productivity")
    
    # Assign unique keys if missing
    if "Key" not in productivity_data.columns:
        productivity_data["Key"] = range(1, len(productivity_data) + 1)
    
    st.subheader("Task Statistics")
    total_tasks = len(productivity_data)
    open_tasks = len(productivity_data[productivity_data["Status"] == "Open"])
    completed_tasks = len(productivity_data[productivity_data["Status"] == "Completed"])
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    st.write(f"Total Tasks: {total_tasks}")
    st.write(f"Open Tasks: {open_tasks}")
    st.write(f"Completed Tasks: {completed_tasks}")
    st.write(f"Completion Rate: {completion_rate:.2f}%")

    st.subheader("80/20 Time Blocking")
    if not productivity_data.empty:
        productivity_data['Due Date'] = pd.to_datetime(productivity_data['Due Date'], errors='coerce')
        today = pd.to_datetime(date.today())
        productivity_data['Days Until Due'] = (productivity_data['Due Date'] - today).dt.days

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

      #  high_value_tasks = sorted_tasks.head(int(len(sorted_tasks) * 0.2))  # Top 20%
        low_value_tasks = sorted_tasks.tail(int(len(sorted_tasks) * 0.8))  # Bottom 80%

        # High-Value Tasks (Only Open or In Progress)
        high_value_tasks = sorted_tasks[(sorted_tasks["Status"].isin(["Open", "In Progress"]))].head(int(len(sorted_tasks) * 0.2))
        st.subheader("🔹 High-Value Tasks (Focus) - 20%")
        st.dataframe(high_value_tasks[['Task Name', 'Priority', 'Due Date', 'Days Until Due', 'Priority Score', 'Status']])
               
        st.subheader("⚠️ Low-Value Tasks (Delegate or Remove) - 80%")
        status_filter = st.selectbox("Filter by Status", ["All", "Open", "In Progress", "Completed"], key="low_value_task_filter")
        if status_filter != "All":
            low_value_tasks = low_value_tasks[low_value_tasks["Status"] == status_filter]
        st.dataframe(low_value_tasks[['Task Name', 'Priority', 'Due Date', 'Days Until Due', 'Priority Score', 'Status']])

    st.subheader("Add New Task")
    with st.form("goal_setting_form", clear_on_submit=True):
        goal_name = st.text_input("Task Name")
        goal_priority = st.selectbox("Priority", ["Low", "Medium", "High"])
        goal_due_date = st.date_input("Due Date")
        add_goal_btn = st.form_submit_button("Add Task")
        if add_goal_btn:
            new_goal = pd.DataFrame([[goal_name, goal_priority, goal_due_date, "Open", ""]], 
                                    columns=["Task Name", "Priority", "Due Date", "Status", "Actual Close Date"])
            new_goal = new_goal.astype(str)
            append_to_google_sheets(new_goal, "Project Management", "Personal Productivity")
            st.success("Task added successfully!")
    
    st.subheader("Update Task Status")
    if not productivity_data.empty and "Task Name" in productivity_data.columns:
        task_options = [f"{index} {row['Task Name']}  {row['Priority']}  {row['Due Date']}" for index, row in productivity_data.iterrows()]
        selected_task = st.selectbox("Select Task to Update", task_options, key="productivity_task_selectbox")
        new_status = st.selectbox("Update Status", ["Not Started", "In Progress", "Completed"], key="productivity_status_selectbox")
        if st.button("Update Task Status"):
            spreadsheet = client.open("Project Management")
            worksheet = spreadsheet.worksheet("Personal Productivity")
            task_index = int(selected_task.split()[0])  # Extract Index
            worksheet.update_cell(task_index + 2, worksheet.find("Status").col, new_status)
            if new_status == "Completed":
                current_date = datetime.now(est).strftime("%Y-%m-%d")
                worksheet.update_cell(task_index + 2, worksheet.find("Actual Close Date").col, current_date)
            st.success(f"Status updated for Task '{selected_task}' to '{new_status}'!")
