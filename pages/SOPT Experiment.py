import streamlit as st
 
st.set_page_config(page_title="Self Order Pointing Task")
project_name = 'sopt'
experiment_URL = "http://selforderedpointingtask.firebaseapp.com/?ver="
# Simulating data for the behavioral task
# participant_ids = get_participant_ids(project_name)

# Title of the app
st.title('Self Order Pointing Task Generator ')
st.text("There are four versions of this task. You can generate your own version of the task by selecting the parameters below.")

objects,abstracts,words,nonwords = st.columns(4)
with objects:
    st.link_button("Objects",experiment_URL+"objects")
    st.image("images/object.jpg",use_container_width=True,clamp=True,width=0.5)

with abstracts:
    st.link_button("Abstracts",experiment_URL+"abstracts")
    st.image("images/abstract.jpg",use_container_width=True,clamp=True,width=0.5)

with words:
    st.link_button("Words",experiment_URL+"words")
    st.image("images/word.jpg",use_container_width=True,clamp=True,width=0.5)

with nonwords:
    st.link_button("Non Words",experiment_URL+"nonwords")
    st.image("images/nonword.jpg",use_container_width=True,clamp=True,width=0.5)

with st.form("experiment"):
    versions = st.multiselect("Versions",['Abstracts','Objects',"Words","Nonwords"])
    tiles = st.multiselect("Tiles",[4,6,8,10,12])
    submitted = st.form_submit_button("Create a new experiment")

if submitted:
    st.link_button("Go to experiment",experiment_URL)

