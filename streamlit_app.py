import folium
from folium import plugins
import pandas as pd
import numpy as np
import streamlit as st

# Load your CSV or data here
# filtered_data = ...

# Sidebar setup
st.sidebar.title("Mode Share Visualization")
modes = ['Car (Driver)', 'Train', 'Bus']  # Example modes
selected_modes = st.sidebar.multiselect("Select Modes", modes, default=modes)

# Allow selecting one mode for colorizing the map
selected_visual_mode = st.sidebar.selectbox("Select Mode to Visualize", selected_modes)

# Function to calculate percentages for the selected mode
def calculate_percentage(selected_mode):
    mode_share_table = filtered_data[filtered_data['Mode'].isin(selected_modes)]
    mode_share_table['Percentage'] = (mode_share_table[selected_mode] / mode_share_table[selected_mode].sum()) * 100
    return mode_share_table

# Color scale
def colorize_map(selected_mode):
    mode_share_table = calculate_percentage(selected_mode)
    min_percentage = mode_share_table['Percentage'].min()
    max_percentage = mode_share_table['Percentage'].max()
    
    # Function to apply color based on percentage
    def get_color(percentage):
        normalized = (percentage - min_percentage) / (max_percentage - min_percentage)
        color = plt.cm.Blues(normalized)  # Using blue color scale
        return f'rgba({int(color[0]*255)}, {int(color[1]*255)}, {int(color[2]*255)}, 0.7)'  # Convert to RGBA

    return mode_share_table, get_color

# Map setup
m = folium.Map(location=[-33.8688, 151.2093], zoom_start=10)  # Example center in Sydney

# Add GeoJSON to the map
geojson_data = ...  # Load your geojson data here

# Style function for GeoJSON based on selected mode's percentage
def style_function(feature):
    sa2_code = feature['properties']['SA2_MAIN16']
    clicked_data = mode_share_table[mode_share_table['SA2_16'] == sa2_code]  # Ensure you match on the correct column
    percentage = clicked_data['Percentage'].values[0] if not clicked_data.empty else 0
    color = get_color(percentage)
    return {
        'fillColor': color,
        'color': 'black',
        'weight': 1,
        'fillOpacity': 0.7,
    }

geojson_layer = folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=['SA2_16', 'SA2_NAME16'])
).add_to(m)

# Display map in Streamlit
st_folium(m, width=1000, height=600)
