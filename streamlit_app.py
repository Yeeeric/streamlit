import streamlit as st
import folium
from streamlit_folium import st_folium
import json

st.title("🗺️ Upload and View GeoJSON Map")

uploaded_file = st.file_uploader("Upload a GeoJSON file", type="geojson")

if uploaded_file is not None:
    try:
        geojson_data = json.load(uploaded_file)

        # Estimate center from first feature
        coords = geojson_data['features'][0]['geometry']['coordinates']
        geom_type = geojson_data['features'][0]['geometry']['type']

        # Handle different geometry types
        if geom_type == "Polygon":
            lon, lat = coords[0][0]
        elif geom_type == "MultiPolygon":
            lon, lat = coords[0][0][0]
        elif geom_type == "Point":
            lon, lat = coords
        else:
            lon, lat = 151.21, -33.87  # fallback: Sydney CBD

        m = folium.Map(location=[lat, lon], zoom_start=10)
        folium.GeoJson(geojson_data, name="Uploaded GeoJSON").add_to(m)

        st_folium(m, width=700, height=500)

    except Exception as e:
        st.error(f"⚠️ Failed to load GeoJSON: {e}")
else:
    st.info("Please upload a `.geojson` file.")
