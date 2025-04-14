import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import random
from datetime import datetime
from millify import millify
from utils.data_utils import get_participant_data
from utils.read_postgres import create_connection
import plotly.express as px
from streamlit_plotly_events import plotly_events

from io import BytesIO
 

st.set_page_config(page_title="Mental Navigation Participant Tracking")

project_name = 'mental-nav'
# Simulating data for the behavioral task
# participant_ids = get_participant_ids(project_name)

# Title of the app
st.title('Mental Navigation Participant Tracking')

subject_view, session_view   = st.tabs(["Subject View","Session View"])
def session_dashboard(completion_code):
    if completion_code:
        try:
            trial, subject, frame, state = get_participant_data(project_name,completion_code)
        except AssertionError:
            st.write("Participant data not found!!!")

        ts = datetime.now().strftime("%Y%m%d_%H%M%S")

        if trial.shape[0]:
            st.download_button(
            label="Download data",
            data=download_data_from_db(trial, subject, frame, state),
            file_name=f"{completion_code}_{ts}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )   

            
            if hasattr(subject,"prolificID"):
                st.metric('Prolific ID',subject['prolificID'].values[0],help='Prolific ID')

            if hasattr(subject,"workerId"):
                st.metric('Worker ID',subject['workerId'].values[0],help='Worker ID')

            if hasattr(subject,"screenHeightcm"):
                st.metric('Screen Height',subject['screenHeightcm'].values[0],help='Worker ID')
            
            day_col,trials_col,acc_col,duration_col, = st.columns(4)
            with day_col:
                st.metric('Session', trial.iloc[0]['block_name'].split(',')[0].strip()[-1],help='Day')
                

            with trials_col:
                st.metric('Trials',millify(trial.shape[0]) ,help='Number of trials')

            with acc_col:
                if hasattr(subject,"acc"):
                    st.metric('Accuracy',millify(subject['acc'].values[0]*100,precision=2)+" %",help='Accuracy')
            
            with duration_col:
                if hasattr(subject,"totalDuration"):
                    st.metric('Total Duration',millify(subject['totalDuration'].values[0]/60,precision=2)+" min",help='Total Duration')

            
            device_survey,landmarks_survey,speed_survey = st.columns(3) 
            with device_survey:
                if hasattr(subject,"device"):
                    st.metric('Device',subject['device'].values[0] ,help='Which device did you use?')
            with landmarks_survey:
                if hasattr(subject,"landmarks"):
                    st.metric('Landmarks', subject['landmarks'].values[0] ,help='How many landmark image are there in the sequence?')
            with speed_survey:
                if hasattr(subject,"speed"):
                    st.metric('Speed', subject['speed'].values[0] ,help='How many speeds were used?')

            if  hasattr(trial,'stepSize'):
                trial = trial[~trial['stepSize'].isna()]
                
                go_df = state[state['stateChange'] == 'GO'].drop_duplicates('trialNumber',keep='first')
                moving_df = state[state['stateChange'] == 'MOVING'].drop_duplicates('trialNumber',keep='first')
                stop_df = state[state['stateChange'] == 'STOP'].drop_duplicates('trialNumber',keep='first')

                # Merge the 'MOVING' and 'STOP' dataframes on 'trialNumber' to compute the duration between 'MOVING' and 'STOP' for each trial
                first_attempt_duration_df = pd.merge(moving_df[['trialNumber', 'stateChangeTime']], stop_df[['trialNumber', 'stateChangeTime']], on='trialNumber', suffixes=('_moving', '_stop'))
                reaction_duration_df = pd.merge(go_df[['trialNumber', 'stateChangeTime']], moving_df[['trialNumber', 'stateChangeTime']], on='trialNumber', suffixes=('_go', '_moving'))

                # Calculate the duration
                first_attempt_duration_df['duration'] = first_attempt_duration_df['stateChangeTime_stop'] - first_attempt_duration_df['stateChangeTime_moving']
                reaction_duration_df['duration'] = reaction_duration_df['stateChangeTime_moving'] - reaction_duration_df['stateChangeTime_go']

                trial['startId'] = trial['pair'].apply(lambda x:x[0])
                trial['targetId'] = trial['pair'].apply(lambda x:x[1])
                interlmdistance = 5
                objectSize = 5

                trial['sessionType'] = trial['train'].apply(lambda x: 'Visual' if x else 'Mental')

                trial['trueTime_s'] = (abs(trial['startId'] - trial['targetId'])*(interlmdistance+objectSize)/trial['stepSize']).round(3)
                trial_sample = trial[['block_name','trialNumber','blockNumber','startId','targetId','attempt','stepSize','trueTime_s','producedTime','train','uid']]
                
                trial_sample['train']  = trial_sample['train'].fillna(False)


                trial_sample.loc[:,'interlmdistance'] = trial_sample['targetId'] - trial_sample['startId'] 
                trial_sample['stepSize'] = pd.Categorical(trial_sample['stepSize'])

                trial_sample['producedTime'] = first_attempt_duration_df['duration']

                trial_sample['producedTime_s'] = (trial_sample['producedTime']/1000).round(3)

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


                # Define 1x speed value
                speed_1x_value = 12.5
                colors = ['#FF0000', '#E32636', '#C71585', '#800080', '#4B0082', '#0000FF']


                # Select boxes
                trial_type = st.selectbox("Trial Type", ['All']+ list(sorted(trial['sessionType'].unique())) )
                speed = st.selectbox("Speed", ["All"] + list(sorted(trial['stepSize'].unique())))

                # Filter by trial type
                if trial_type != 'All':
                    if trial_type == "Mental":
                        trial_sample = trial_sample[~trial_sample['train']]
                    elif trial_type == "Visual":
                        trial_sample = trial_sample[trial_sample['train']]

                # Filter by speed if not "All"
                if speed != "All":
                    trial_sample = trial_sample[trial_sample['stepSize'] == speed]

                # Process each step size
                step_sizes = trial_sample['stepSize'].unique()
                print(step_sizes)

                speed_err_prod = {}
                speed_err_reac = {}

                for step in step_sizes:
                    speed_data = trial_sample[trial_sample['stepSize'] == step]
                    
                    speed_err_prod[step] = speed_data.groupby('trueTime_dir').agg(
                        mean_produced_time=('producedTime_s', 'mean'),
                        std_produced_time=('producedTime_s', 'std')).reset_index()
                    
                    speed_err_reac[step] = speed_data[speed_data['reactionTime_s'] < 5].groupby('trueTime_dir').agg(
                        mean_reaction_time=('reactionTime_s', 'mean'),
                        std_reaction_time=('reactionTime_s', 'std')).reset_index()
                    
                    speed_err_prod[step]['dir'] = speed_err_prod[step]['trueTime_dir'] / speed_err_prod[step]['trueTime_dir'].abs()
                    speed_err_prod[step]['mean_produced_time'] = speed_err_prod[step]['mean_produced_time'] * speed_err_prod[step]['dir']

                # Plot
                fig, ax = plt.subplots()

                for i, step in enumerate(step_sizes):
                    if speed == "All" or speed == step:
                        label = f"{(step / speed_1x_value):.1f} x"
                        colors = colors if len(step_sizes)>2 else [colors[0],colors[-1]]
                        color = colors[i]
                        ax = trial_sample[trial_sample['stepSize'] == step].plot(
                            x='jitter_trueTime_dir', y='producedTime_dir', kind='scatter', ax=ax, label=label, alpha=0.5, s=5, c=color)
                        ax.errorbar(
                            x=speed_err_prod[step]['trueTime_dir'], 
                            y=speed_err_prod[step]['mean_produced_time'], 
                            fmt='o', alpha=0.5, yerr=speed_err_prod[step]['std_produced_time'], c=color)

                ax.plot([-8, 8], [-8, 8], c='grey', linewidth=0.5, linestyle=(5, (10, 3)))
                ax.tick_params(axis='x', rotation=45)
                ax.tick_params(axis='y', rotation=45)
                ax.legend(loc='upper left')
                ax.set_xlabel("True Time (s)")
                ax.set_ylabel("Produced Time (s)")
                st.subheader('Comparison of True and Produced Time')
                st.pyplot(fig)


                fig, ax = plt.subplots()

                for i, step in enumerate(step_sizes):
                    if speed == "All" or speed == step:
                        label = f"{(step / speed_1x_value):.1f} x"
                        color = colors[i % len(colors)]
                        ax = trial_sample[trial_sample['stepSize'] == step].plot(
                            y='reactionTime_s', x='jitter_trueTime_dir', kind='scatter', ax=ax, label=label, alpha=0.7, s=5, c=color)
                        ax.errorbar(
                            x=speed_err_reac[step]['trueTime_dir'], 
                            y=speed_err_reac[step]['mean_reaction_time'], 
                            fmt='o', alpha=0.5, c=color)

                ax.set_ylim([0, 5])
                ax.tick_params(axis='x', rotation=45)
                ax.tick_params(axis='y', rotation=45)
                ax.legend(loc='upper left')
                ax.set_xlabel("True Time (s)")
                ax.set_ylabel("Reaction Time (s)")
                st.subheader('Reaction Time vs True Time')
                st.pyplot(fig)

        else:
            st.text("There is no data for the given completion code.")
        # # my id
        # # iVlJesYYgNZSQkHm0LGCmUa97vmk
        # # cu88XFr1jQMM9gQXPEKMPXawUXM2


@st.cache_data
def get_subject(prolificID):
    engine = create_connection()
    with engine.connect() as conn:
        df = pd.read_sql(f"""select * from raw_subjects where "prolificID"='{prolificID}' order by date ;""",conn)
        conn.close()
        return df
 
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


# Sidebar for user selection
# completion_code = st.sidebar.selectbox('Select a Participant', participant_ids)
# st.markdown(f"### Subject ID:  \n **{completion_code}**")

# with subject_view:
#     try:
#         engine = create_connection()
#         with engine.connect() as conn:

#                 participant_ids = pd.read_sql("""select distinct("prolificID") from raw_subjects""",conn)
#                 subject_id = st.selectbox("Select a subject",participant_ids['prolificID'].values)
#                 if subject_id:
#                     subject = get_subject(subject_id)
#                     subject['acc_'] = subject['acc'].mul(100).round(2).astype(str) + "%"
#                     subject['day'] = subject['day'].astype(str)

#                     fig = px.line(subject, x='day', y='acc_', markers=True, color_discrete_sequence=["#9b59b6"],
#                                 hover_data={"uid": True, "day": False,"date":True, "acc_": True})   
                    
#                     fig.add_hline(y='30',line_width=0.8,line_dash='dash')

#                     fig.update_traces(marker=dict(size=10))

#                     # Set x-axis and y-axis limits
#                     fig.update_layout(
#                         yaxis_title="Accuracy",
#                         xaxis_title="Session",
#                         xaxis=dict(range=[0.8, 5.2]),  
#                         yaxis=dict(range=[0, 100]),
                        
#                     )

#                     selected_points = plotly_events(fig)

                    
#                     if selected_points:
                        
#                         completion_code = subject[subject['day']==str(selected_points[0]['x'])]['uid'].values[0]
#                         session_dashboard(completion_code)
#     except Exception as e:
#         print(e)
#         st.text("No data")

 

with session_view:

    completion_code = st.text_input("Enter session completion code")

    session_dashboard(completion_code)