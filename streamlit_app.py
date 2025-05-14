import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from folium import Choropleth, GeoJsonTooltip
import json
from branca.colormap import linear

# File paths
geojson_path = "data/sa2.geojson"
csv_path = "data/data_Mode_Census_UR_SA2.csv"

# Load data
with open(geojson_path, "r", encoding="utf-8") as f:
    sa2_geojson = json.load(f)

df = pd.read_csv(csv_path)

# Sidebar mode selection
mode_columns = [col for col in df.columns if col not in ['SA2_16_CODE', 'SA2_16']]
selected_mode = st.sidebar.selectbox("Select a travel mode", mode_columns)

# Map SA2 code to percentage for selected mode
percentage_by_sa2 = dict(zip(df["SA2_16_CODE"], df[selected_mode]))

# Add percentage as a new property to each GeoJSON feature
for feature in sa2_geojson["features"]:
    sa2_code = feature["properties"]["SA2_MAIN16"]
    pct = percentage_by_sa2.get(sa2_code, 0)
    feature["properties"]["PERCENTAGE"] = f"{pct:.1f}%"
    feature["properties"]["PERCENTAGE_FLOAT"] = pct  # For color scale

# Set up color scale
pct_values = list(percentage_by_sa2.values())
colormap = linear.Blues_09.scale(min(pct_values), max(pct_values))
colormap.caption = f"{selected_mode} mode share (%)"

# Define style for each feature
def style_function(feature):
    pct = feature["properties"]["PERCENTAGE_FLOAT"]
    return {
        "fillColor": colormap(pct),
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.7,
    }

# Initialize Folium map
m = folium.Map(location=[-25.2744, 133.7751], zoom_start=4, tiles="cartodbpositron")

# Add choropleth layer
folium.GeoJson(
    sa2_geojson,
    style_function=style_function,
    tooltip=GeoJsonTooltip(
        fields=["SA2_NAME16", "PERCENTAGE"],
        aliases=["SA2: ", f"{selected_mode}:"],
        labels=True,
        sticky=False
    )
).add_to(m)

# Add color legend
colormap.add_to(m)

# Render map
st_data = st_folium(m, width=700, height=600)

# Show breakdown if a zone is clicked
if st_data and st_data.get("last_active_drawing"):
    clicked_code = st_data["last_active_drawing"]["properties"]["SA2_MAIN16"]
    clicked_name = st_data["last_active_drawing"]["properties"]["SA2_NAME16"]
    st.markdown(f"### Mode share in {clicked_name}")
    breakdown = df[df["SA2_16_CODE"] == clicked_code].T
    breakdown = breakdown.reset_index()
    breakdown.columns = ["Mode", "Percentage"]
    breakdown = breakdown[~breakdown["Mode"].isin(["SA2_16_CODE", "SA2_16"])]
    breakdown["Percentage"] = breakdown["Percentage"].astype(float).map("{:.1f}%".format)
    st.dataframe(breakdown, use_container_width=True)
