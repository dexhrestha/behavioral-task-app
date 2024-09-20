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

trial_sample['producedTime_s'] = (trial_sample['producedTime']/1000).round(3)
trial_sample['trueTime_s'] = (trial_sample['trueTime']/1000).round(3)

#producedtime_with_direction
trial_sample['producedTime_dir'] = (trial_sample['interlmdistance']/trial_sample['interlmdistance'].apply(abs)*trial_sample['producedTime_s'])
#truetime_with_direction
trial_sample['trueTime_dir'] = (trial_sample['interlmdistance']/trial_sample['interlmdistance'].apply(abs)*trial_sample['trueTime_s'])

# add jitter
trial_sample.loc[:,'jitter_producedTime_dir'] =  trial_sample['producedTime_dir'].apply(lambda x:x + random.uniform(-0.05, 0.05))
trial_sample.loc[:,'jitter_trueTime_dir'] = trial_sample['trueTime_dir'].apply(lambda x:x + random.uniform(-0.05, 0.05))

# calcualte reaction time with jitter
trial_sample['reactionTime_s'] = (reaction_duration_df['duration']/1000).round(3)
trial_sample.loc[:,'jitter_reactionTime_s'] = trial_sample['reactionTime_s'].apply(lambda x:x + random.uniform(-0.05, 0.05))

speed_1 = trial_sample[trial_sample['stepSize']==20]
speed_2 = trial_sample[trial_sample['stepSize']==15]


trial_type = st.selectbox("Trial Type",['All','Mental','Visual'])

if trial_type!='All':
    if trial_type=="Mental":
        trial_sample = trial_sample[~trial_sample['isTrain']]
    elif trial_type=="Visual":
        trial_sample = trial_sample[trial_sample['isTrain']]


speed_1_err_prod = speed_1.groupby('trueTime_dir').agg(mean_produced_time=('producedTime_s', 'mean'),
                                                  std_produced_time=('producedTime_s', 'std')).reset_index()

speed_1_err_reac = speed_1[speed_1['reactionTime_s']<5].groupby('trueTime_dir').agg(mean_reaction_time=('reactionTime_s', 'mean'),
                                                  std_reaction_time=('reactionTime_s', 'std')).reset_index()
                                         

speed_1_err_prod['dir'] = speed_1_err_prod['trueTime_dir'] / speed_1_err_prod['trueTime_dir'].abs()
speed_1_err_prod['mean_produced_time'] = speed_1_err_prod['mean_produced_time'] * speed_1_err_prod['dir']


speed_2_err_prod = speed_2.groupby('trueTime_dir').agg(mean_produced_time=('producedTime_s', 'mean'),
                                                  std_produced_time=('producedTime_s', 'std')).reset_index()

speed_2_err_reac = speed_2[speed_2['reactionTime_s']<5].groupby('trueTime_dir').agg(mean_reaction_time=('reactionTime_s', 'mean'),
                                                  std_reaction_time=('reactionTime_s', 'std')).reset_index()
                                         

speed_2_err_prod['dir'] = speed_2_err_prod['trueTime_dir'] / speed_2_err_prod['trueTime_dir'].abs()
speed_2_err_prod['mean_produced_time'] = speed_2_err_prod['mean_produced_time'] * speed_2_err_prod['dir']


fig, ax = plt.subplots()


ax = speed_1.plot(x='jitter_trueTime_dir',y='producedTime_dir',kind='scatter',c='red',ax=ax,label='1x',alpha=0.5,s=5)
ax.errorbar(x=speed_1_err_prod['trueTime_dir'],y=speed_1_err_prod['mean_produced_time'],c='red',fmt='o',alpha=0.5,yerr=speed_1_err_prod['std_produced_time'])

ax = speed_2.plot(x='jitter_trueTime_dir',y='producedTime_dir',kind='scatter',c='blue',ax=ax,label='0.75x',alpha=0.5,s=5)
ax.errorbar(x=speed_2_err_prod['trueTime_dir'],y=speed_2_err_prod['mean_produced_time'],c='blue',fmt='o',alpha=0.5,yerr=speed_2_err_prod['std_produced_time'])

plt.plot([-6,6],[-6,6],c='grey',linewidth=0.5,linestyle=(5,(10,3)),ax=ax)


ax.tick_params(axis='x', rotation=45)
ax.tick_params(axis='y', rotation=45)
ax.legend(loc='upper left')
ax.set_xlabel("True Time (s)")
ax.set_ylabel("Produced Time (s)")
st.subheader('Comparison of True and Produced Time')
st.pyplot(fig)

fig ,ax = plt.subplots()
ax = speed_1.plot(y='reactionTime_s',x='jitter_trueTime_dir',kind='scatter',c='red',ax=ax,label='1x',alpha=0.7,s=5)
ax.errorbar(x=speed_1_err_reac['trueTime_dir'],y=speed_1_err_reac['mean_reaction_time'],c='red',fmt='o',alpha=0.5)

ax = speed_2[speed_2['reactionTime_s']<=5].plot(y='reactionTime_s',x='jitter_trueTime_dir',kind='scatter',c='blue',ax=ax,label='0.75x',alpha=0.7,s=5)
ax.errorbar(x=speed_2_err_reac['trueTime_dir'],y=speed_2_err_reac['mean_reaction_time'],c='blue',fmt='o',alpha=0.5)

ax.set_ylim([0,5])
ax.tick_params(axis='x', rotation=45)
ax.tick_params(axis='y', rotation=45)
ax.legend(loc='upper left')
ax.set_xlabel("True Time (s)")
ax.set_ylabel("Reaction Time (s)")
st.subheader('Reaction Time vs True Time')
st.pyplot(fig)

# # my id
# # iVlJesYYgNZSQkHm0LGCmUa97vmk
# # cu88XFr1jQMM9gQXPEKMPXawUXM2