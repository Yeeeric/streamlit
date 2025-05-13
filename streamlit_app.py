# streamlit_app.py

import streamlit as st
import geopandas as gpd
import folium
from streamlit_folium import st_folium

st.title("🗺️ Shapefile Viewer")

# Upload shapefile components
uploaded_files = st.file_uploader("Upload shapefile components (.shp, .shx, .dbf, etc)", accept_multiple_files=True, type=['shp', 'shx', 'dbf', 'prj'])

if uploaded_files:
    # Save uploaded files to disk for GeoPandas to read
    import os
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        for uploaded_file in uploaded_files:
            with open(os.path.join(tmpdir, uploaded_file.name), "wb") as f:
                f.write(uploaded_file.getbuffer())

        # Find .shp file
        shp_path = [os.path.join(tmpdir, f.name) for f in uploaded_files if f.name.endswith('.shp')][0]
        
        # Load with geopandas
        gdf = gpd.read_file(shp_path)
        st.write("Shapefile loaded successfully!")
        st.dataframe(gdf.head())

        # Plot with Folium
        m = folium.Map(location=[gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()], zoom_start=10)
        folium.GeoJson(gdf).add_to(m)

        st_folium(m, width=700, height=500)
