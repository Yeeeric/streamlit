# streamlit_app.py

import streamlit as st
import folium
from streamlit_folium import st_folium
import json

st.title("🗺️ Fast GeoJSON Map Viewer")

# Load GeoJSON
with open("data/your_file.geojson") as f:
    geojson_data = json.load(f)

# Create Map
m = folium.Map(location=[-33.87, 151.21], zoom_start=10)
folium.GeoJson(geojson_data).add_to(m)

# Display Map
st_folium(m, width=700, height=500)
