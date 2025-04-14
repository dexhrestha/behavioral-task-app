import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

import statsmodels.api as sm


import pandas as pd
import numpy as np
from matplotlib import cm
import matplotlib.pyplot as plt

from matplotlib.colors import LinearSegmentedColormap

# Define the bluered colormap
colors = [
    (0.0, "#ff0000"),
    (1.0, "#0000ff"),
]
bluered_cmap = LinearSegmentedColormap.from_list("plotly_bluered", colors)

 

import seaborn as sns
from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

def filter_dataframe(df:pd.DataFrame):
    modify = st.sidebar.checkbox("Add filters")
    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.sidebar.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Treat columns with < 10 unique values as categorical
            if is_categorical_dtype(df[column]) or df[column].nunique() < 10:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df

df_orig = pd.read_csv('mentalnavigation.csv')

jitter_strength = 0.05  # Adjust as needed

df_orig.loc[:,'absta'] = df_orig['trueDuration_ms'] / 1000.
df_orig.loc[:,'abstp'] = df_orig['producedDuration_ms'] / 1000.

df_orig.loc[:,'lmdistance'] = df_orig['startId']-df_orig['targetId']
df_orig.loc[:,'lmdistance'] = df_orig['lmdistance']/ df_orig['lmdistance'].abs()
df_orig.loc[:,'ta'] = df_orig['absta']*df_orig['lmdistance']
df_orig.loc[:,'tp'] = df_orig['abstp']*df_orig['lmdistance']



df_orig.loc[:,'absDistance'] = abs(df_orig['startId']-df_orig['targetId'])
df_orig.loc[:,'absError'] = abs(df_orig['tp'] - df_orig['ta'])

df_orig.loc[:,'ta_jittered'] = df_orig['ta'] + np.random.uniform(-jitter_strength, jitter_strength, size=len(df_orig))
df_orig.loc[:,'tp_jittered'] = df_orig['tp'] + np.random.uniform(-jitter_strength, jitter_strength, size=len(df_orig))


df_orig['subjectId'] = pd.Categorical(df_orig['subjectId'])
df_orig['absDistance'] = pd.to_numeric(df_orig['absDistance'])
 


st.title("Mental Navigation Analysis Pipeline")

st.markdown("""
## Summary
We want to understand the effect of speed on variability of produced time. According to Weber's law, the relation between standard deviation and distance is linear. Does this linearity hold while learning to produce time at multiple speeds?  
To answer this question we will:
""")
df = filter_dataframe(df_orig)

st.markdown("### 1. Relation between standard deviation and mean time")
st.markdown("We want to check if the relation between standard deviation and mean time. Lets visualize this using a scatter plot.")



# Group without normalization first
stats = df.groupby(["speed", "absta"])["abstp"].agg(["mean", "std"]).reset_index()

# Normalize 'absta' in the grouped stats
stats['absta_normalized'] = (stats['absta'] - stats['absta'].min()) / (stats['absta'].max() - stats['absta'].min())

# Compute the coefficients using the normalized version
stats['cv'] = stats['std'] / stats['mean']

stats['absta_sq'] = stats['absta'] ** 2

# Step 2: Group by speed and fit linear models
weber_by_speed = []

# Group by 'speed' and fit the same model per group
for speed, group in stats.groupby('speed'):
    group['mean_sq'] = group['mean'] ** 2
    group['var'] = group['std'] ** 2

    X = sm.add_constant(group['mean_sq'])
    y = group['var']

    model = sm.OLS(y, X).fit()
    k = model.params['mean_sq']
    weber_by_speed.append({'speed': speed, 'weber_coefficient': k})

# Convert to DataFrame for plotting
weber_df = pd.DataFrame(weber_by_speed)
st.dataframe(weber_df)
 

st.dataframe(stats)
# Get 6 evenly spaced colors from the RdBu colormap
unique_speeds = stats['speed'].sort_values().unique()
n_colors = len(unique_speeds)
abs_palette = [bluered_cmap(i) for i in np.linspace(0, 1, n_colors)][::-1]
color_palette = dict(zip(unique_speeds,abs_palette))
sns.set_palette(abs_palette)
# Sample from RdBu excluding the center (avoid white)
# e.g., use 0 to 0.4 and 0.6 to 1 to skip the middle
# Create a linspace that avoids the middle
sample_points = np.linspace(0, 0.4, n_colors // 2).tolist() + np.linspace(0.6, 1, n_colors - n_colors // 2).tolist()

colors = [
    f'rgb({int(r*255)},{int(g*255)},{int(b*255)})'
    for r, g, b, _ in [bluered_cmap(p) for p in sample_points]
]
colors = colors[::-1]

# Create figure
fig = go.Figure()

# Get sorted unique speed values to keep colors consistent
unique_speeds = sorted(stats['speed'].unique())

for i, speed in enumerate(unique_speeds):
    filtered = stats[stats['speed'] == speed]
    
    fig.add_trace(
        go.Scatter(
            x=filtered['mean'],
            y=filtered['std'],
            mode='lines+markers',
            name=f'Speed: {speed}',
            line=dict(color=colors[i], width=3),
            marker=dict(size=6, color=colors[i]),
            hoverinfo='x+y+name',
            showlegend=True
        )
    )

fig.update_layout(
    title="Standard deviation vs Mean of produced time",
    xaxis_title="Time (s)",
    yaxis_title="SD"
)


st.plotly_chart(fig)

fig, ax = plt.subplots()
 
filtered_speeds = st.multiselect("speed", unique_speeds, unique_speeds)

if filtered_speeds:
    filtered_stats = stats[stats['speed'].isin(filtered_speeds)]
else:
    filtered_stats = stats.copy(deep=True)

# Plot a regression line for each selected speed
for speed in  filtered_speeds:
    sns.regplot(data=filtered_stats[filtered_stats['speed']==speed], x='mean', y='std', label=speed, ax=ax, color=color_palette[speed] , ci=False,scatter=True,   
            scatter_kws={'s': 40, 'alpha': 0.6},  # make points visible
            line_kws={'linewidth': 2})

ax.legend()
ax.set_title("Regression plot for standard deviation vs mean of produced time")
ax.set_xlabel("Time (s)")
ax.set_ylabel("SD")
st.pyplot(fig)



st.markdown("""
            
This visualization clearly shows linear relation between standard deviation and mean. We can also see that as speed increases standard deviation is decreasing suggesting that participants are consistent at faster speeds.  
This is consistent with Weber's law which states that   
> **the Just noticable difference(JND) between two stimuli is proportional to the magnitude of the original stimuli.**
$$
\\frac{\sigma}{\mu} = k
$$
Now the question we are interested in is: does weber's law hold for multiple speed?
            """)

st.markdown("### 2. Relation between Coefficient of Variation (CV) and Mean Time")
# st.markdown("In this analysis, we aim to investigate whether the relationship between the Coefficient of Variation (CV) and mean time remains consistent across different speeds. The CV is a measure of relative variability, which expresses the ratio of the standard deviation to the mean. If weber's law holds")
st.markdown("To answer the question whether weber's law holds for multiple speed we look at the relation between coefficient if variation(CV) and mean of produced time. CV measures the relative variability expressed as the ratio of standard deviation to the mean. If weber's law holds true for different speeds, CV should be constant for all durations.")


# Create figure
fig = go.Figure()

# Get sorted unique speed values to keep colors consistent
unique_speeds = sorted(stats['speed'].unique())

for i, speed in enumerate(unique_speeds):
    filtered = stats[stats['speed'] == speed]
    
    fig.add_trace(
        go.Scatter(
            x=filtered['mean'],
            y=filtered['cv'],
            mode='lines+markers',
            name=f'Speed: {speed}',
            line=dict(color=colors[i], width=3),
            marker=dict(size=6, color=colors[i]),
            hoverinfo='x+y+name',
            showlegend=True
        )
    )

fig.update_layout(
    title="CV (Slope vs mean time) vs mean of produced time ",
    xaxis_title="Time (s)",
    yaxis_title="CV"
)


st.plotly_chart(fig)

st.markdown("### 3. Relation between Weber Coefficient and Speed")


fig, ax = plt.subplots()
# Create a scatter plot
 
 

# # Assuming 'stats' is your dataframe and you have columns 'speed', 'weber'
# sns.scatterplot(data=stats, x='speed', y='weber', ax=ax, hue='speed', palette=abs_palette[::-1])

# Add error bars
# Here, we are assuming that 'weber' has a normal distribution, so we can calculate standard deviation
# For simplicity, let's use the standard deviation of 'weber' grouped by 'speed' as an example of error.

# Calculate mean and std deviation for each 'speed'
 

fig, ax = plt.subplots()
grouped_stats = stats.groupby('speed')['cv'].agg(['mean', 'std'])
# Loop through each unique 'speed' value and add error bars
for i,speed in enumerate(unique_speeds):
    mean_value = grouped_stats.loc[speed, 'mean']
    std_value = grouped_stats.loc[speed, 'std']
    print(mean_value,std_value)
    # Plotting error bars (yerr is the error bars)
    ax.errorbar(speed, mean_value, yerr=std_value, fmt='o', color=abs_palette[i], capsize=5)
# Display the plot in the Streamlit app
plt.ylabel("CV")
plt.xlabel("Speed")
plt.title("CV vs speed")
st.pyplot(fig)

#slope of variances vs t squared
st.markdown("""
            # Weber's Coefficient as slope of variance vs t^2 
            """)

 

X = weber_df['speed']
y = weber_df['weber_coefficient']
trend_model = sm.OLS(y, X).fit()

# Predict values for plotting the trend line
weber_df['trend'] = trend_model.predict(X)

# Plotting with regression line and confidence interval (error bars using bootstrap)
fig = plt.figure(figsize=(8, 5))
for speed in unique_speeds:
    sns.regplot(data=weber_df[weber_df['speed']==speed], x='speed', y='weber_coefficient',color=color_palette[speed], scatter_kws={'s': 60}, line_kws={'color': 'red'},ci=False)
sns.scatterplot(weber_df,x='speed',y='trend',color='black')
plt.title('Weber Coefficient vs. Speed with Regression Fit')
plt.ylabel('Weber Coefficient (k)')
plt.xlabel('Speed')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.show()

st.pyplot(fig)

fig = plt.figure()
df['speed'].value_counts().plot(kind='bar')
st.pyplot(fig)