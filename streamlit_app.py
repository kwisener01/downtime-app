# Initialize tabs
tab1, tab2, tab3, tab4 = st.tabs(["Downtime Issues", "KPI Dashboard", "Personal Productivity", "Task Delegation"])

### Task Delegation ###
with tab4:
    st.header("📌 Task Delegation")

    task_data = load_from_google_sheets("Project Management", "Task Delegation")

    if not task_data.empty:
        st.subheader("📋 Task List")
        st.dataframe(task_data)

        st.subheader("📝 Update Task Status")
        task_options = task_data["Task Name"].dropna().tolist() if "Task Name" in task_data.columns else []
        if task_options:
            selected_task = st.selectbox("Select Task to Update", task_options)
            new_status = st.selectbox("Update Status", ["Not Started", "In Progress", "Completed"])
            if st.button("Update Task Status"):
                spreadsheet = client.open("Project Management")
                worksheet = spreadsheet.worksheet("Task Delegation")
                data = worksheet.get_all_records()
                for i, row in enumerate(data, start=2):
                    if row["Task Name"] == selected_task:
                        status_col_index = worksheet.find("Status").col
                        worksheet.update_cell(i, status_col_index, new_status)
                        st.success(f"Status updated for '{selected_task}' to '{new_status}'!")
                        break
        else:
            st.warning("No 'Task Name' column found in the data.")
    else:
        st.warning("No task data found.")

    st.subheader("➕ Assign New Task")
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
