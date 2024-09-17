import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random
from datetime import datetime

from utils.data_utils import get_participant_data,get_participant_ids

from io import BytesIO
 

st.set_page_config(page_title="Behavioral Data Dashboard")

# Simulating data for the behavioral task
participant_ids = get_participant_ids()

# Title of the app
st.title('Behavioral Task: True vs Produced Time')


# Sidebar for user selection
selected_user = st.sidebar.selectbox('Select a Participant', participant_ids)
st.markdown(f"### Subject ID:  \n **{selected_user}**")

trial, subject, frame, state = get_participant_data(selected_user)

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


st.download_button(
    label="Download data",
    data=download_data_from_db(trial, subject, frame, state),
    file_name=f"{selected_user}_{ts}.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)



go_df = state[state['stateChange'] == 'GO'].drop_duplicates('trialNumber',keep='first')
moving_df = state[state['stateChange'] == 'MOVING'].drop_duplicates('trialNumber',keep='first')
stop_df = state[state['stateChange'] == 'STOP'].drop_duplicates('trialNumber',keep='first')

# Merge the 'MOVING' and 'STOP' dataframes on 'trialNumber' to compute the duration between 'MOVING' and 'STOP' for each trial
first_attempt_duration_df = pd.merge(moving_df[['trialNumber', 'stateChangeTime']], stop_df[['trialNumber', 'stateChangeTime']], on='trialNumber', suffixes=('_moving', '_stop'))
reaction_duration_df = pd.merge(go_df[['trialNumber', 'stateChangeTime']], moving_df[['trialNumber', 'stateChangeTime']], on='trialNumber', suffixes=('_go', '_moving'))

# Calculate the duration
first_attempt_duration_df['duration'] = first_attempt_duration_df['stateChangeTime_stop'] - first_attempt_duration_df['stateChangeTime_moving']
reaction_duration_df['duration'] = reaction_duration_df['stateChangeTime_moving'] - reaction_duration_df['stateChangeTime_go']


trial_sample = trial[['trialNumber','blockNumber','startId','targetId','attempt','stepSize','isTrain','subject','trueTime','producedTime']]
trial_sample.loc[:,'interlmdistance'] = trial_sample['targetId'] - trial_sample['startId'] 
trial_sample['stepSize'] = pd.Categorical(trial_sample['stepSize'])

trial_sample['producedTime'] = first_attempt_duration_df['duration']

trial_sample['producedTime'] = (trial_sample['interlmdistance']/trial_sample['interlmdistance'].apply(abs)*trial_sample['producedTime'])/1000
trial_sample['trueTime'] = (trial_sample['interlmdistance']/trial_sample['interlmdistance'].apply(abs)*trial_sample['trueTime'])/1000
trial_sample['reactionTime'] = reaction_duration_df['duration']/1000
trial_sample.loc[:,'jitter_producedTime'] =  trial_sample['producedTime'].apply(lambda x:x + random.uniform(-0.25, 0.25))
trial_sample.loc[:,'jitter_reactionTime'] = trial_sample['reactionTime'].apply(lambda x:x + random.uniform(-0.25, 0.25))
trial_sample.loc[:,'jitter_trueTime'] = trial_sample['trueTime'].apply(lambda x:x + random.uniform(-0.25, 0.25))


trial_type = st.selectbox("Trial Type",['All','Mental','Visual'])

if trial_type!='All':
    if trial_type=="Mental":
        trial_sample = trial_sample[~trial_sample['isTrain']]
    elif trial_type=="Visual":
        trial_sample = trial_sample[trial_sample['isTrain']]

fig ,ax = plt.subplots()

speed_1 = trial_sample[trial_sample['stepSize']==20]
speed_2 = trial_sample[trial_sample['stepSize']==15]

ax = speed_1.plot(y='trueTime',x='jitter_producedTime',kind='scatter',c='red',ax=ax,label='1x',alpha=0.7)
ax = speed_2.plot(y='trueTime',x='jitter_producedTime',kind='scatter',c='blue',ax=ax,label='0.75x',alpha=0.7)
ax.tick_params(axis='x', rotation=45)
ax.tick_params(axis='y', rotation=45)
ax.legend(loc='upper left')
ax.set_ylabel("True Time (s)")
ax.set_xlabel("Produced Time (s)")
st.subheader('Comparison of True and Produced Time')
st.pyplot(fig)

fig ,ax = plt.subplots()
ax = speed_1.plot(y='reactionTime',x='jitter_trueTime',kind='scatter',c='red',ax=ax,label='1x',alpha=0.7)
ax = speed_2.plot(y='reactionTime',x='jitter_trueTime',kind='scatter',c='blue',ax=ax,label='0.75x',alpha=0.7)
ax.tick_params(axis='x', rotation=45)
ax.tick_params(axis='y', rotation=45)
ax.legend(loc='upper left')
ax.set_xlabel("True Time (s)")
ax.set_ylabel("Reaction Time (s)")
ax.set_ylim([0,trial_sample['reactionTime'].max()+1])
st.subheader('Reaction Time vs True Time')
st.pyplot(fig)

# # my id
# # iVlJesYYgNZSQkHm0LGCmUa97vmk
# # cu88XFr1jQMM9gQXPEKMPXawUXM2