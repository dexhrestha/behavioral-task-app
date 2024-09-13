import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random
from utils.data_utils import get_participant_data,get_participant_ids



# Simulating data for the behavioral task
participant_ids = get_participant_ids()

# Title of the app
st.title('Behavioral Task: True vs Produced Time')

# Sidebar for user selection
selected_user = st.sidebar.selectbox('Select a Participant', participant_ids)

trial, subject, frame, state = get_participant_data(selected_user)

trial_sample = trial[['trialNumber','blockNumber','startId','targetId','attempt','stepSize','isTrain','subject','trueTime','producedTime']]
trial_sample.loc[:,'jitter_trueTime'] =  trial_sample['trueTime'].apply(lambda x:x + random.uniform(-250, 250))
trial_sample.loc[:,'interlmdistance'] = trial_sample['targetId'] - trial_sample['startId'] 
trial_sample['stepSize'] = pd.Categorical(trial_sample['stepSize']);

fig ,ax = plt.subplots()

speed_1 = trial_sample[trial_sample['stepSize']==20]
ax = speed_1.plot(x='jitter_trueTime',y='producedTime',kind='scatter',marker='o',colormap='coolwarm',c='interlmdistance',ax=ax,label='20')
ax.collections[0].colorbar.remove()
speed_2 = trial_sample[trial_sample['stepSize']==15]
ax = speed_2.plot(x='jitter_trueTime',y='producedTime',kind='scatter',marker='^',colormap='coolwarm',c='interlmdistance',ax=ax,label='15')
ax.set_xticks(range(0,7000,500))
ax.set_yticks(range(0,7000,500))
ax.tick_params(axis='x', rotation=45)
ax.tick_params(axis='y', rotation=45)
ax.legend(loc='upper left')
ax.set_xlabel("True Time (ms)")
ax.set_ylabel("Produced Time (ms)")
st.subheader('Comparison of True and Produced Time')
st.pyplot(fig)

# my id
# iVlJesYYgNZSQkHm0LGCmUa97vmk