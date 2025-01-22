import streamlit as st
import pandas as pd

# Title of the app
st.title("Recurring Data Analysis")

# File uploader
uploaded_file = st.file_uploader("Upload your checksheet CSV file", type=["csv"])

if uploaded_file is not None:
    # Load the CSV file into a DataFrame
    data = pd.read_csv(uploaded_file)

    # Display the raw data
    st.subheader("Raw Data")
    st.dataframe(data)

    # Analyze recurring data points
    recurring_data = data.groupby(['Process Name', 'Defect Type']).agg(
        Count=('Defect Type', 'count'),
        Average_Time_to_Resolve=('Time to Resolve (Minutes)', 'mean'),
        Resolved_Count=('Resolved (Y/N)', lambda x: sum(x == 'Y'))
    ).reset_index()

    # Display analysis results
    st.subheader("Recurring Data Analysis")
    st.dataframe(recurring_data)

    # Visualize defect trends
    st.subheader("Defect Type Trends")
    defect_counts = recurring_data.groupby("Defect Type")["Count"].sum()
    st.bar_chart(defect_counts)

    # Visualize process trends
    st.subheader("Process Name Trends")
    process_counts = recurring_data.groupby("Process Name")["Count"].sum()
    st.bar_chart(process_counts)

else:
    st.info("Please upload a CSV file to start the analysis.")
