import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from branca.colormap import LinearColormap
import json
import numpy as np

# Set up page config
st.set_page_config(layout="wide")
st.title("Travel Mode Share by SA2")

# Load data
@st.cache_data
def load_data():
    mode_share = pd.read_csv("data/data_Mode_Census_UR_SA2.csv")
    geojson_data = json.load(open("data/sa2.geojson"))
    return mode_share, geojson_data

mode_share_df, geojson_data_raw = load_data()

# Ensure geojson is JSON serializable (convert numpy types to native Python types)
def make_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(v) for v in obj]
    elif isinstance(obj, (np.integer, np.floating)):
        return obj.item()
    return obj

geojson_data = make_json_serializable(geojson_data_raw)

# Sidebar filter
modes = [col for col in mode_share_df.columns if col not in ["sa2_code", "sa2_name", "total_persons"]]
selected_mode = st.sidebar.selectbox("Select travel mode", modes)

# Merge mode share with GeoJSON properties
mode_share_map = {row["sa2_code"]: row[selected_mode] for _, row in mode_share_df.iterrows()}

# Determine min/max values for color scale
min_val = min(mode_share_map.values())
max_val = max(mode_share_map.values())

# Define color scale
colormap = LinearColormap(
    colors=["#ffffcc", "#41b6c4", "#253494"],
    vmin=min_val,
    vmax=max_val,
    caption=f"{selected_mode} mode share (%)"
)

# Create map
m = folium.Map(location=[-25.2744, 133.7751], zoom_start=4, tiles="cartodbpositron")

# Define style function for each feature
def style_function(feature):
    sa2_code = feature["properties"]["SA2_MAINCODE_2021"]
    value = mode_share_map.get(sa2_code, 0)
    return {
        "fillOpacity": 0.7,
        "weight": 0.5,
        "color": "black",
        "fillColor": colormap(value)
    }

# Add GeoJSON layer
geojson_layer = folium.GeoJson(
    geojson_data,
    name="SA2s",
    style_function=style_function,
    highlight_function=lambda x: {"weight": 2, "fillOpacity": 0.9},
    tooltip=folium.GeoJsonTooltip(
        fields=["SA2_NAME_2021"],
        aliases=["SA2:"],
        sticky=True
    )
)
geojson_layer.add_to(m)

# Add color legend
colormap.add_to(m)

# Display map and capture click
st_data = st_folium(m, width=1000, height=600)

# Show clicked feature info
if st_data and st_data.get("last_active_drawing", None):
    clicked_props = st_data["last_active_drawing"]["properties"]
    sa2_code = clicked_props["SA2_MAINCODE_2021"]
    sa2_name = clicked_props["SA2_NAME_2021"]
    selected_value = mode_share_map.get(sa2_code, None)

    if selected_value is not None:
        st.markdown(f"### {sa2_name}")
        st.metric(f"{selected_mode} mode share (%)", f"{selected_value:.2f}")
    else:
        st.warning("No data available for the selected SA2.")
