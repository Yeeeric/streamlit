import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

st.set_page_config(layout="wide")
st.title("🚶‍♂️ Mode Share (% of Total Travel) by SA2")

# === Load data ===
csv_path = "data/data_Mode_Census_UR_SA2.csv"
geojson_path = "data/sa2.geojson"

df = pd.read_csv(csv_path, dtype={"SA2_16_CODE": str})
with open(geojson_path) as f:
    geojson_data = json.load(f)

# === Sidebar UI: Clean vertical checkbox list ===
st.sidebar.markdown("### Select Mode(s):")
available_modes = sorted(df["Mode"].unique())
selected_modes = []
for mode in available_modes:
    if st.sidebar.checkbox(mode, value=True):
        selected_modes.append(mode)

# === Calculate % mode share per SA2 ===

# Total persons by SA2 (denominator)
total_by_sa2 = df.groupby("SA2_16_CODE")["Persons"].sum().rename("TotalPersons")

# Selected modes by SA2 (numerator)
selected_df = df[df["Mode"].isin(selected_modes)]
selected_by_sa2 = selected_df.groupby("SA2_16_CODE")["Persons"].sum().rename("SelectedPersons")

# Combine and compute share
mode_share_df = pd.concat([total_by_sa2, selected_by_sa2], axis=1).fillna(0)
mode_share_df["PercentShare"] = (mode_share_df["SelectedPersons"] / mode_share_df["TotalPersons"]) * 100

# Build lookup
share_lookup = mode_share_df["PercentShare"].to_dict()

# Add to GeoJSON
for feature in geojson_data["features"]:
    sa2_code = feature["properties"]["SA2_MAIN16"]
    percent = share_lookup.get(sa2_code)
    feature["properties"]["PercentShare"] = round(percent, 2) if pd.notna(percent) else None

# === Define map scale ===
valid_vals = mode_share_df["PercentShare"].dropna()
vmin, vmax = valid_vals.min(), valid_vals.max()

colormap = LinearColormap(colors=["#e0f3db", "#a8ddb5", "#43a2ca", "#0868ac"], vmin=0, vmax=100)
colormap.caption = "% Share of Selected Modes"

# === Sydney-centered map (shifted west slightly) ===
SYDNEY_COORDS = [-33.87, 151.05]

if "map_center" not in st.session_state:
    st.session_state["map_center"] = SYDNEY_COORDS
if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"] = 10

# === Map and styling ===
m = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"], control_scale=True)
colormap.add_to(m)

def style_function(feature):
    value = feature["properties"].get("PercentShare")
    if value is None:
        return {"fillOpacity": 0}
    return {
        "fillColor": colormap(value),
        "color": "black",
        "weight": 0.3,
        "fillOpacity": 0.7,
    }

tooltip = folium.GeoJsonTooltip(
    fields=["SA2_NAME16", "SA2_MAIN16", "PercentShare"],
    aliases=["SA2 Name:", "SA2 Code:", "Selected Mode Share (%)"],
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

# === Show map and preserve state ===
map_data = st_folium(m, width=900, height=650)

if map_data and "center" in map_data and "zoom" in map_data:
    st.session_state["map_center"] = [map_data["center"]["lat"], map_data["center"]["lng"]]
    st.session_state["map_zoom"] = map_data["zoom"]

# === Show detailed mode breakdown for clicked SA2 ===
clicked_sa2 = None

if map_data and "last_active_drawing" in map_data and map_data["last_active_drawing"]:
    clicked_props = map_data["last_active_drawing"]["properties"]
    clicked_sa2 = clicked_props.get("SA2_MAIN16")
    clicked_name = clicked_props.get("SA2_NAME16")

if clicked_sa2:
    st.subheader(f"🚏 Mode Share Breakdown for {clicked_name} (SA2 {clicked_sa2})")

    # Filter data for clicked SA2
    sa2_df = df[df["SA2_16_CODE"] == clicked_sa2].copy()

    if not sa2_df.empty:
        total_persons = sa2_df["Persons"].sum()
        sa2_df["Share (%)"] = (sa2_df["Persons"] / total_persons * 100).round(2)
        sa2_df = sa2_df[["Mode", "Persons", "Share (%)"]].sort_values("Persons", ascending=False)
        st.dataframe(sa2_df, use_container_width=True)
    else:
        st.info("No data available for this SA2.")

