import streamlit as st
import pandas as pd
import folium
import json
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

# Load the data files
mode_share = pd.read_csv("data/data_Mode_Census_UR_SA2.csv")
geojson_data = json.load(open("data/sa2.geojson"))

# Sidebar mode selection
modes = mode_share["Mode"].unique()  # Correct capitalization for "Mode"
selected_mode = st.sidebar.selectbox("Select a mode of transport", sorted(modes))

# Filter data by selected mode
filtered_data = mode_share[mode_share["Mode"] == selected_mode]

# Generate a folium map centered around a specific point (example: Sydney)
m = folium.Map(location=[-33.8688, 151.2093], zoom_start=12)

# Add GeoJSON layer to the map
geojson_layer = folium.GeoJson(geojson_data).add_to(m)

# Create a color scale from white to blue, with null values set to transparent
colormap = LinearColormap(colors=['white', 'blue'], vmin=filtered_data['Persons'].min(), vmax=filtered_data['Persons'].max())

# Function to add style to GeoJSON features
def style_function(feature):
    # Match the SA2 code with the geojson data
    sa2_code = feature['properties']['SA2_16_CODE']  # Correct capitalization for "SA2_16_CODE"
    person_count = filtered_data[filtered_data['SA2_16_CODE'] == sa2_code]['Persons'].values[0] if not filtered_data[filtered_data['SA2_16_CODE'] == sa2_code].empty else None
    if person_count is None:
        # If person_count is None (null), make the area transparent
        return {
            'fillColor': 'transparent',
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.0
        }
    else:
        # Otherwise, use the color scale from white to blue
        return {
            'fillColor': colormap(person_count),
            'color': 'black',
            'weight': 1,
            'fillOpacity': 0.7
        }

# Apply style to GeoJSON features
geojson_layer = folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(fields=['SA2_16', 'SA2_16_CODE'], aliases=['Name:', 'Code:'])  # Correct capitalization for "SA2_16" and "SA2_16_CODE"
).add_to(m)

# Display map in Streamlit
st_data = st_folium(m, width=1000, height=600)

# Mode share table on the right side
st.sidebar.title(f"Mode Share for {selected_mode}")
st.sidebar.write("Mode Share Breakdown:")

# Create a table for the mode share data
mode_share_table = filtered_data[['SA2_16', 'Persons', 'Ratio']]  # Correct column names
mode_share_table['Percentage'] = (mode_share_table['Persons'] / mode_share_table['Ratio']) * 100  # Calculation for percentage
mode_share_table = mode_share_table[['SA2_16', 'Persons', 'Percentage']]

# Show the table on the sidebar
st.sidebar.write(mode_share_table)

# When a zone is clicked, display detailed mode share breakdown
if st_data and st_data.get("last_active_drawing", None):
    clicked_feature = st_data["last_active_drawing"]
    clicked_sa2_code = clicked_feature['properties']['SA2_16_CODE']  # Correct capitalization for "SA2_16_CODE"
    
    # Find the clicked SA2 in the filtered data
    clicked_data = filtered_data[filtered_data['SA2_16_CODE'] == clicked_sa2_code]
    
    # Display the mode share breakdown for the clicked SA2
    if not clicked_data.empty:
        clicked_name = clicked_data['SA2_16'].values[0]  # Correct column name for "SA2_16"
        clicked_persons = clicked_data['Persons'].values[0]  # Correct column name for "Persons"
        clicked_ratio = clicked_data['Ratio'].values[0]  # Correct column name for "Ratio"
        clicked_percentage = (clicked_persons / clicked_ratio) * 100
        
        st.sidebar.subheader(f"Mode Share Breakdown for {clicked_name}")
        st.sidebar.write(f"Persons: {clicked_persons}")
        st.sidebar.write(f"Total Ratio: {clicked_ratio}")
        st.sidebar.write(f"Mode Share Percentage: {clicked_percentage:.2f}%")
