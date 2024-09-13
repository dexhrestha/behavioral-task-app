import streamlit as st
import pandas as pd
import numpy as np

# Simulating data for the behavioral task
np.random.seed(42)
participant_ids = [f"User_{i}" for i in range(1, 11)]  # 10 users
true_time = np.random.uniform(10, 20, size=10)  # True time between 10 and 20 seconds
produced_time = true_time + np.random.uniform(-2, 2, size=10)  # Produced time with some variation

# Creating a DataFrame to hold the data
data = pd.DataFrame({
    'Participant': participant_ids,
    'True Time (s)': true_time,
    'Produced Time (s)': produced_time
})

# Title of the app
st.title('Behavioral Task: True vs Produced Time')

# Sidebar for user selection
selected_user = st.sidebar.selectbox('Select a Participant', participant_ids)

# Filter the data based on the selected user
user_data = data[data['Participant'] == selected_user]

# Display the selected user's data
st.subheader(f"Data for {selected_user}")
st.write(user_data)

# Optionally, you can visualize the difference between true and produced time using a bar chart
st.subheader('Comparison of True and Produced Time')
st.bar_chart(user_data[['True Time (s)', 'Produced Time (s)']].T)

