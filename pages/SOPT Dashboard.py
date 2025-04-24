import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random
from datetime import datetime

from utils.data_utils import get_participant_data

from io import BytesIO
 

st.set_page_config(page_title="Self Order Pointing")
project_name = 'sopt'
experiment_URL = "http://selforderedpointingtask.firebaseapp.com/?ver="
# Simulating data for the behavioral task
# participant_ids = get_participant_ids(project_name)

# Title of the app
st.title('Self Order Pointing Task')
 

# Sidebar for user selection
# selected_user = st.sidebar.selectbox('Select a Participant', participant_ids)
# st.markdown(f"### Subject ID:  \n **{selected_user}**")
selected_user = st.text_input("Select a user")



ts = datetime.now().strftime("%Y%m%d_%H%M%S")

@st.cache_data
def download_data_from_db(trial,subject,frame,state):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        trial.to_excel(writer, "trial")
        subject.to_excel(writer, "subject")
        frame.to_excel(writer, "frame")
        state.to_excel(writer, "state")
    output.seek(0)  # Reset pointer to the start of the stream
    return output   

@st.cache_data
def process_trials(df):
    df['prev_selected'] = df['prev_selected'].fillna(0).astype(int)
    df['error'] = df.duplicated(subset=['blockTrial','selectedImage'],keep='first')

    return df


if selected_user:
    try:
        trial, subject, frame, state = get_participant_data(project_name,selected_user)
    except AssertionError:
        st.write("Participant data not found!!!")

    processed_trials = process_trials(trial)
    st.download_button(
        label="Download data",
        data=download_data_from_db(processed_trials, subject, frame, state),
        file_name=f"{selected_user}_{ts}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    processed_trials = processed_trials[['trialNumber','blockNumber','blockTrial','responseTime','error','numTiles','pageNumber']]
    processed_trials['responseTime_s'] = processed_trials['responseTime']/1000.

    total_time, total_trials = st.columns(2)

    with total_time:
        st.metric("Total Tine",str(round(float(processed_trials['responseTime_s'].sum()),2))+' s')

    with total_trials:
        st.metric("Total Trials",processed_trials.shape[0])

    st.table(processed_trials)

    
    # Create the figure and axis
    fig, ax = plt.subplots(figsize=(10, 5))  # Adjust size if needed

    # Generate the bar plot
    error_data = processed_trials.groupby(['numTiles', 'blockTrial'])['error'].sum()
    error_data.plot(kind='bar', ax=ax)

    # Set title and labels
    ax.set_title("Number of Errors Across Trials", fontsize=14)
    ax.set_xlabel("Trials (Block Trial)", fontsize=12)
    ax.set_ylabel("Error Count", fontsize=12)
    

    # Set x-tick labels as blockTrial values
    ax.set_xticklabels([f"{idx[1]}" for idx in error_data.index], rotation=0, ha="right")

    st.markdown("## Sample Visualizations")
    # Display the plot in Streamlit
    st.pyplot(fig)
    




# ids :
    # JKqowBchDRXfPI59CWjfJN46Hz02
    # 10V6r5kdjTTwtBDacmjqtYsw3512
    # ujYMAO8B8KhUdB6ZHmY333nQSIu1
    # 35USuHJIWAojvzNvYCegnQQvQKCO
    
