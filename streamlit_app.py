import streamlit as st
import pandas as pd
import numpy as np
import json
import folium
from streamlit_folium import st_folium
from branca.colormap import LinearColormap
from folium.features import GeoJsonTooltip

# Load data
mode_share = pd.read_csv("data/data_Mode_Census_UR_SA2.csv")
with open("data/sa2.geojson") as f:
    geojson_data = json.load(f)

# Sidebar mode selection
modes = mode_share["mode"].unique()
selected_mode = st.sidebar.selectbox("Select a mode of transport", sorted(modes))

# Filter data by selected mode
df_mode = mode_share[mode_share["mode"] == selected_mode].copy()

# Calculate mode share percentage
df_mode["mode_share_pct"] = df_mode["persons"] / df_mode["total_persons"] * 100

# Merge with GeoJSON
geojson_map = {}
for feature in geojson_data["features"]:
    sa2_code = str(feature["properties"]["sa2_16_code"])
    geojson_map[sa2_code] = feature
    feature["properties"]["mode_share_pct"] = None
    feature["properties"]["persons"] = None
    feature["properties"]["total_persons"] = None
    feature["properties"]["mode"] = None

for _, row in df_mode.iterrows():
    sa2_code = str(row["sa2_16_code"])
    if sa2_code in geojson_map:
        geojson_map[sa2_code]["properties"]["mode_share_pct"] = round(row["mode_share_pct"], 2)
        geojson_map[sa2_code]["properties"]["persons"] = int(row["persons"])
        geojson_map[sa2_code]["properties"]["total_persons"] = int(row["total_persons"])
        geojson_map[sa2_code]["properties"]["mode"] = row["mode"]

# Define color scale
mode_values = df_mode["mode_share_pct"].dropna()
min_val, max_val = mode_values.min(), mode_values.max()
colormap = LinearColormap(colors=["#ffffcc", "#41b6c4", "#253494"], vmin=min_val, vmax=max_val)
colormap.caption = f"{selected_mode} mode share (%)"

# Create map
m = folium.Map(location=[-25.2744, 133.7751], zoom_start=4, tiles="cartodbpositron")

def style_function(feature):
    pct = feature["properties"]["mode_share_pct"]
    return {
        "fillOpacity": 0.7,
        "weight": 0.3,
        "color": "black",
        "fillColor": colormap(pct) if pct is not None else "#d3d3d3",
    }

tooltip = GeoJsonTooltip(
    fields=["sa2_16", "mode", "mode_share_pct", "persons", "total_persons"],
    aliases=["SA2", "Mode", "Mode share (%)", "Persons", "Total persons"],
    localize=True,
    sticky=False,
    labels=True,
)

geojson_layer = folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=tooltip,
    name="Mode Share",
)

geojson_layer.add_to(m)
colormap.add_to(m)

# Display map in Streamlit
st_data = st_folium(m, width=1000, height=600)

# Clickable feature display
if st_data and st_data.get("last_active_drawing", None):
    props = st_data["last_active_drawing"]["properties"]
    st.subheader(f"{props['sa2_16']}")
    st.markdown(f"""
    - **Mode**: {props['mode']}
    - **Mode Share**: {props['mode_share_pct']}%
    - **Persons**: {props['persons']}
    - **Total Persons**: {props['total_persons']}
    """)
