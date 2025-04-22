import streamlit as st
 
st.set_page_config(page_title="Self Order Pointing Task")
project_name = 'sopt'
experiment_URL = "http://selforderedpointingtask.firebaseapp.com/?ver="
# Simulating data for the behavioral task
# participant_ids = get_participant_ids(project_name)

# Title of the app
st.title('Self Order Pointing Task Dashboard ')
st.text("There are four versions of this task.")
st.markdown("Experiment Links")

objects,abstracts,words,nonwords = st.columns(4)
with objects:
    st.link_button("Objects",experiment_URL+"objects")
    st.image("images/object.jpg",use_column_width=True,clamp=True,width=0.5)

with abstracts:
    st.link_button("Abstracts",experiment_URL+"abstracts")
    st.image("images/abstract.jpg",use_column_width=True,clamp=True,width=0.5)

with words:
    st.link_button("Words",experiment_URL+"words")
    st.image("images/word.jpg",use_column_width=True,clamp=True,width=0.5)

# with nonwords:
#     st.link_button("Non Words",experiment_URL+"nonwords")
#     st.image("images/nonword.jpg",use_column_width=True,clamp=True,width=0.5)
