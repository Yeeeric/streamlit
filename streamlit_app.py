import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

st.set_page_config(layout="wide")
st.title("🗺️ CO₂ Emissions by SA2 (Sydney)")

# Load data
csv_path = "data/SA_CO2_totals.csv"
geojson_path = "data/sa2.geojson"

df = pd.read_csv(csv_path, dtype={"SA2_16_CODE": str})
with open(geojson_path) as f:
    geojson_data = json.load(f)

# Center map around Sydney GCCSA
SYDNEY_COORDS = [-33.8688, 151.2093]

# Merge CO2_total into GeoJSON properties for tooltip
co2_map = df.set_index("SA2_16_CODE")["CO2_total"].to_dict()
for feature in geojson_data["features"]:
    sa2_code = feature["properties"]["SA2_MAIN16"]
    co2_value = co2_map.get(sa2_code)
    feature["properties"]["CO2_total"] = co2_value if pd.notna(co2_value) else None

# Filter based on CO2_total slider
min_val = df["CO2_total"].min()
max_val = df["CO2_total"].max()
selected_range = st.slider("Filter by CO₂ total (tonnes)", float(min_val), float(max_val), (float(min_val), float(max_val)))

# Create map
m = folium.Map(location=SYDNEY_COORDS, zoom_start=10)

# Custom color scale (red → yellow → green, reversed for high CO2 = red)
colormap = LinearColormap(colors=["green", "yellow", "red"], vmin=min_val, vmax=max_val)
colormap.caption = "CO₂ Total (tonnes)"
colormap.add_to(m)

# Add GeoJson with filtering and color logic
def style_function(feature):
    value = feature["properties"]["CO2_total"]
    if value is None or not (selected_range[0] <= value <= selected_range[1]):
        return {"fillOpacity": 0}
    else:
        return {
            "fillColor": colormap(value),
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.7,
        }

tooltip = folium.GeoJsonTooltip(
    fields=["SA2_NAME16", "SA2_MAIN16", "CO2_total"],
    aliases=["SA2 Name:", "SA2 Code:", "CO₂ Total (tonnes):"],
    localize=True,
    sticky=False,
    labels=True,
)

folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=tooltip,
    name="CO2 Choropleth"
).add_to(m)

# Display map
st_data = st_folium(m, width=900, height=650)
