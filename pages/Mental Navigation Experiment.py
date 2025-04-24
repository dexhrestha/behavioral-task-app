import streamlit as st
from urllib.parse import urlencode


st.set_page_config(page_title="Mental Navigation Task")
project_name = 'mental-nav'
experiment_URL = "http://mentalnavigation.firebaseapp.com/?"
# Simulating data for the behavioral task
# participant_ids = get_participant_ids(project_name)

# Title of the app
st.title('Mental Navigation Task Generator')


def generate_experiment_link(url,params):
    query_string = urlencode(params)
    separator = '&' if '?' in url else '?'
    return url + separator + query_string if params else url

with st.form('experiment'):
    imageset = st.selectbox("Imageset", [1,2,3])
    trainingStepSizes = st.multiselect("Training Step Sizes", [12.5, 15, 17.5, 20], default=[12.5, 15])
    testingStepSizes = st.multiselect("Testing Step Sizes", [10, 12.5, 15, 17.5, 22.5, 27.5, 30], default=[10, 12.5, 15, 17.5, 22.5, 27.5])
    numLandmarks = st.slider("Number of Landmarks", value=9,min_value=2,max_value=9)
    day = st.selectbox("Day", [1, 2, 3, 4, 5])
    screenHeightcm = st.number_input("Screen Height (cm)", value=21.24)
    if day<3:
        numTrialPairs = st.slider("Number of Trial Pairs",max_value=int(numLandmarks*(numLandmarks-1)/2))
        initialTrials = st.slider("Initial Trials", max_value=100)
    

    submitted = st.form_submit_button("Submit")

    if submitted:
        formData = {
            "imageset": imageset,
 
            "trainingStepSizes": ",".join(map(str, trainingStepSizes)),
            "testingStepSizes": ",".join(map(str, testingStepSizes)),
            "numTrialPairs": numTrialPairs,
            "numLandmarks": numLandmarks,
            "initialTrials": initialTrials,
 
            "screenHeightcm": screenHeightcm,

            "DAY": day
        }

if submitted:
    st.link_button("Go to experiment", generate_experiment_link(experiment_URL,  formData))
 