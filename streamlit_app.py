import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

st.set_page_config(layout="wide")
st.title("🗺️ Mode Share by SA2 (Sydney)")

# === Load data ===
csv_path = "data/data_Mode_Census_UR_SA2.csv"
geojson_path = "data/sa2_simplified.geojson"  # assumed simplified already

df = pd.read_csv(csv_path, dtype={"SA2_16_CODE": str})
with open(geojson_path) as f:
    geojson_data = json.load(f)

# === Sidebar filter ===
available_modes = sorted(df["Mode"].unique())
selected_modes = st.sidebar.multiselect("Select Mode(s):", available_modes, default=available_modes)

# === Aggregate mode share per SA2 ===
filtered_df = df[df["Mode"].isin(selected_modes)]
mode_summary = (
    filtered_df
    .groupby("SA2_16_CODE", as_index=False)["Persons"]
    .sum()
    .rename(columns={"Persons": "TotalPersons"})
)

# === Build lookup for GeoJSON merge ===
mode_map = mode_summary.set_index("SA2_16_CODE")["TotalPersons"].to_dict()

# Add mode share values to GeoJSON properties
for feature in geojson_data["features"]:
    sa2_code = feature["properties"]["SA2_MAIN16"]
    persons = mode_map.get(sa2_code)
    feature["properties"]["TotalPersons"] = persons if pd.notna(persons) else None

# === Get bounds for choropleth range ===
valid_vals = mode_summary["TotalPersons"].dropna()
vmin, vmax = valid_vals.min(), valid_vals.max()

# === Sydney initial view (slightly west) ===
SYDNEY_COORDS = [-33.87, 151.05]  # moved west from 151.21

# === Use session state to preserve zoom/pan ===
if "map_center" not in st.session_state:
    st.session_state["map_center"] = SYDNEY_COORDS
if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"] = 10

# === Color scale ===
colormap = LinearColormap(colors=["green", "yellow", "red"], vmin=vmin, vmax=vmax)
colormap.caption = "Total Persons by Selected Mode(s)"

# === Build Folium map ===
m = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"], control_scale=True)
colormap.add_to(m)

def style_function(feature):
    value = feature["properties"]["TotalPersons"]
    if value is None:
        return {"fillOpacity": 0}
    return {
        "fillColor": colormap(value),
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.7,
    }

tooltip = folium.GeoJsonTooltip(
    fields=["SA2_NAME16", "SA2_MAIN16", "TotalPersons"],
    aliases=["SA2 Name:", "SA2 Code:", "Total Persons (Selected Modes):"],
    localize=True,
    sticky=False,
    labels=True,
)

folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=tooltip,
    name="Mode Share Choropleth"
).add_to(m)

# === Display and preserve map state ===
map_data = st_folium(m, width=900, height=650)

if map_data and "center" in map_data and "zoom" in map_data:
    st.session_state["map_center"] = [map_data["center"]["lat"], map_data["center"]["lng"]]
    st.session_state["map_zoom"] = map_data["zoom"]
