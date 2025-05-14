import streamlit as st
import pandas as pd
import folium
import json
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

# Load the data files
mode_share = pd.read_csv("data/data_Mode_Census_UR_SA2.csv")
geojson_data = json.load(open("data/sa2.geojson"))

# Check the structure of the GeoJSON data (for debugging purposes)
st.write("GeoJSON Properties Example:")
st.write(geojson_data['features'][0]['properties'])  # Display the properties of the first feature

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
    sa2_code = feature['properties']['SA2_MAIN16']  # Updated to use 'SA2_MAIN16'
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
    clicked_sa2_code = clicked_feature['properties']['SA2_MAIN16']  # Updated to 'SA2_MAIN16'
    clicked_sa2_name = clicked_feature['properties']['SA2_NAME16']  # Updated to 'SA2_NAME16'
    clicked_data = filtered_data[filtered_data['SA2_16'] == clicked_sa2_name]
    st.write(f"Detailed Mode Share for {clicked_sa2_name} (Code: {clicked_sa2_code})")
    st.write(clicked_data)
