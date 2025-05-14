import streamlit as st
import pandas as pd
import folium
import json
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

# Load the data files
mode_share = pd.read_csv("data/data_Mode_Census_UR_SA2.csv")
geojson_data = json.load(open("data/sa2.geojson"))

# Sidebar mode selection - Checkbox for each mode with a 'select all' option
modes = mode_share["Mode"].unique()
select_all = st.sidebar.checkbox("Select All Modes", value=False)
selected_modes = []

if select_all:
    selected_modes = modes.tolist()
else:
    for mode in modes:
        if st.sidebar.checkbox(mode, value=False):  # By default, all are deselected
            selected_modes.append(mode)

# Filter data by selected modes
filtered_data = mode_share[mode_share["Mode"].isin(selected_modes)]

# Calculate the percentage based on selected modes
if not filtered_data.empty:
    mode_share_table = filtered_data[['SA2_16', 'Persons', 'Ratio']]  # Correct column names
    mode_share_table['Percentage'] = (mode_share_table['Persons'] / filtered_data['Persons'].sum()) * 100  # Percentage of selected modes
else:
    mode_share_table = pd.DataFrame(columns=['SA2_16', 'Persons', 'Percentage'])

# Sidebar table for mode share data
st.sidebar.title(f"Mode Share for {', '.join(selected_modes) if selected_modes else 'None selected'}")
st.sidebar.write(mode_share_table)

# Create a folium map centered around a specific point (example: Sydney)
m = folium.Map(location=[-33.8688, 151.2093], zoom_start=12)

# Add GeoJSON layer to the map
geojson_layer = folium.GeoJson(geojson_data).add_to(m)

# Create a color scale from white to blue, with null values set to transparent
colormap = LinearColormap(colors=['white', 'blue'], vmin=filtered_data['Persons'].min() if not filtered_data.empty else 0, 
                           vmax=filtered_data['Persons'].max() if not filtered_data.empty else 0)

# Function to add style to GeoJSON features
def style_function(feature):
    # Match the SA2 code with the geojson data
    sa2_code = feature['properties']['SA2_MAIN16']
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
    tooltip=folium.GeoJsonTooltip(fields=['SA2_NAME16', 'SA2_MAIN16'], aliases=['Name:', 'Code:'])  # Updated to 'SA2_NAME16'
).add_to(m)

# Display map in Streamlit
st_data = st_folium(m, width=1000, height=600)

# When a zone is clicked, display detailed mode share breakdown
if st_data and st_data.get("last_active_drawing", None):
    clicked_feature = st_data["last_active_drawing"]
    clicked_sa2_code = clicked_feature['properties']['SA2_MAIN16']  # Updated to 'SA2_MAIN16'
    clicked_sa2_name = clicked_feature['properties']['SA2_NAME16']  # Updated to 'SA2_NAME16'
    
    # Get data for clicked zone (filter by SA2 code)
    clicked_data = filtered_data[filtered_data['SA2_16'] == clicked_sa2_name]
    
    if not clicked_data.empty:
        st.write(f"Detailed Mode Share for {clicked_sa2_name} (Code: {clicked_sa2_code})")
        st.write(clicked_data[['SA2_16', 'Persons', 'Mode', 'Percentage']])  # Show relevant columns
    else:
        st.write("No data available for the selected zone.")
