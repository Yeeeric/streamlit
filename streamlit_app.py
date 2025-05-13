import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium

st.title("🗺️ CO₂ Emissions by SA2")

# Load data
csv_path = "data/SA2_CO2_totals.csv"
geojson_path = "data/sa2.geojson"

try:
    df = pd.read_csv(csv_path, dtype={"SA2_16_CODE": str})
    with open(geojson_path) as f:
        geojson_data = json.load(f)

    # Create base map
    m = folium.Map(location=[-25.2744, 133.7751], zoom_start=4)  # center of Australia

    # Add Choropleth layer
    choropleth = folium.Choropleth(
        geo_data=geojson_data,
        name="choropleth",
        data=df,
        columns=["SA2_16_CODE", "CO2_total"],
        key_on="feature.properties.SA2_MAIN16",
        fill_color="YlOrRd",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="CO₂ Total",
    ).add_to(m)

    # Add hover tooltip
    folium.GeoJsonTooltip(fields=["SA2_NAME16", "SA2_MAIN16"]).add_to(choropleth.geojson)

    # Show map
    st_folium(m, width=800, height=600)

except Exception as e:
    st.error(f"❌ Failed to render map: {e}")
