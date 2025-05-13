import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

# Configure page layout
st.set_page_config(layout="wide")
st.title("🚶‍♂️ Mode Share by SA2")

# === Load data ===
df = pd.read_csv("data/data_Mode_Census_UR_SA2.csv", dtype={"SA2_16_CODE": str})
with open("data/sa2.geojson") as f:
    geojson_data = json.load(f)

# === Sidebar mode selection with select all/deselect all ===
modes = sorted(df["Mode"].unique())

# Set up session state
if "selected_modes" not in st.session_state:
    st.session_state.selected_modes = modes.copy()
if "select_all" not in st.session_state:
    st.session_state.select_all = True
if "map_center" not in st.session_state:
    st.session_state.map_center = [-33.87, 151.05]  # Slightly west of Sydney to avoid ocean
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 10
if "clicked_sa2" not in st.session_state:
    st.session_state.clicked_sa2 = None

# Sidebar filter
st.sidebar.markdown("### Travel Modes")
if st.sidebar.button("✅ Select All" if not st.session_state.select_all else "❌ Deselect All"):
    st.session_state.select_all = not st.session_state.select_all
    st.session_state.selected_modes = modes.copy() if st.session_state.select_all else []

new_selection = []
for mode in modes:
    if st.sidebar.checkbox(mode, value=mode in st.session_state.selected_modes, key=mode):
        new_selection.append(mode)

# Update selection state
if new_selection != st.session_state.selected_modes:
    st.session_state.selected_modes = new_selection

# === Prepare aggregated data ===
selected_df = df[df["Mode"].isin(st.session_state.selected_modes)]
grouped = selected_df.groupby("SA2_16_CODE")["Persons"].sum().rename("SelectedPersons")
lookup = grouped.to_dict()

# Inject data into GeoJSON
for feature in geojson_data["features"]:
    sa2_code = feature["properties"]["SA2_MAIN16"]
    val = lookup.get(sa2_code)
    feature["properties"]["PercentShare"] = round(val, 2) if pd.notna(val) else None

# === Create folium map ===
m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom, control_scale=True)

colormap = LinearColormap(["#e5f5e0", "#31a354"], vmin=0, vmax=max(lookup.values(), default=1))
colormap.caption = "% Mode Share"
colormap.add_to(m)

def style_function(feature):
    val = feature["properties"].get("PercentShare")
    return {
        "fillColor": colormap(val) if val is not None else "transparent",
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.7 if val is not None else 0,
    }

tooltip = folium.GeoJsonTooltip(
    fields=["SA2_NAME16", "SA2_MAIN16", "PercentShare"],
    aliases=["SA2 Name:", "SA2 Code:", "Selected Mode Share (%)"],
)

geojson_layer = folium.GeoJson(
    geojson_data,
    style_function=style_function,
    tooltip=tooltip,
    name="Mode Share Layer"
)
geojson_layer.add_to(m)

# === Display map and handle clicks ===
col1, col2 = st.columns([2, 1])

with col1:
    map_data = st_folium(m, width=800, height=600)

    # Preserve zoom and center
    if map_data and "center" in map_data and "zoom" in map_data:
        st.session_state.map_center = [map_data["center"]["lat"], map_data["center"]["lng"]]
        st.session_state.map_zoom = map_data["zoom"]

    # Track clicked SA2
    if map_data and "last_active_drawing" in map_data and map_data["last_active_drawing"]:
        props = map_data["last_active_drawing"]["properties"]
        clicked_code = props.get("SA2_MAIN16")
        clicked_name = props.get("SA2_NAME16")
        st.session_state.clicked_sa2 = (clicked_code, clicked_name)

# === Mode share table (right panel) ===
with col2:
    if st.session_state.clicked_sa2:
        sa2_code, sa2_name = st.session_state.clicked_sa2
        st.markdown(f"### 📊 Mode Share for {sa2_name}")

        sa2_df = df[(df["SA2_16_CODE"] == sa2_code) & (df["Mode"].isin(st.session_state.selected_modes))].copy()
        total = sa2_df["Persons"].sum()

        if total > 0:
            sa2_df["% Share"] = (sa2_df["Persons"] / total * 100).round(2)
            sa2_df = sa2_df[["Mode", "Persons", "% Share"]].sort_values("Persons", ascending=False)
            st.dataframe(sa2_df, use_container_width=True)
        else:
            st.info("No data for selected modes in this SA2.")
