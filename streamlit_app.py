import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

# Set page config
st.set_page_config(layout="wide")

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv("data/data_Mode_Census_UR_SA2.csv")
    gdf = gpd.read_file("data/sa2.geojson")
    return df, gdf

df, gdf = load_data()

# Get unique modes
all_modes = df["Mode"].unique().tolist()
all_modes.sort()

# Sidebar filters
with st.sidebar:
    st.header("Filter by Mode")

    if "selected_modes" not in st.session_state:
        st.session_state.selected_modes = all_modes.copy()

    # Select/Deselect all buttons
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("Select All"):
            st.session_state.selected_modes = all_modes.copy()
    with col2:
        if st.button("Deselect All"):
            st.session_state.selected_modes = []

    # Mode checkbox list
    selected = []
    for mode in all_modes:
        checked = mode in st.session_state.selected_modes
        if st.checkbox(mode, checked=checked):
            selected.append(mode)
    st.session_state.selected_modes = selected

# Skip rest of app if nothing selected
if not st.session_state.selected_modes:
    st.warning("Please select at least one mode to view the map.")
    st.stop()

# Calculate % share of selected modes per SA2
selected_df = df[df["Mode"].isin(st.session_state.selected_modes)]
sa2_total_selected = selected_df.groupby("SA2_16_CODE")["Persons"].sum().rename("Selected")
sa2_total_all = df.groupby("SA2_16_CODE")["Persons"].sum().rename("AllModes")
merged = pd.concat([sa2_total_selected, sa2_total_all], axis=1)
merged["PercentShare"] = (merged["Selected"] / merged["AllModes"] * 100).round(2)
lookup_percent = merged["PercentShare"].to_dict()

# Add PercentShare property to GeoJSON
gdf["PercentShare"] = gdf["SA2_MAIN16"].map(lookup_percent)

# Create Folium map
m = folium.Map(
    location=[-33.86, 151.0],  # Slightly west of Sydney CBD
    zoom_start=10,
    control_scale=True,
    prefer_canvas=True,
)

# Define colormap
max_percent = max(lookup_percent.values(), default=100)
colormap = LinearColormap(
    colors=["#e5f5e0", "#31a354"],
    vmin=0,
    vmax=max(100, max_percent),
).to_step(10)
colormap.caption = "Selected Mode Share (%)"
colormap.add_to(m)

# Highlight selected zone
highlight_function = lambda x: {"weight": 2, "fillOpacity": 0.7, "color": "black"}

# Tooltip fields
tooltip = folium.GeoJsonTooltip(
    fields=["SA2_NAME16", "SA2_MAIN16", "PercentShare"],
    aliases=["SA2 Name:", "SA2 Code:", "Selected Mode Share (%)"],
    localize=True
)

# Inject GeoJSON into map
geojson = folium.GeoJson(
    gdf,
    name="SA2 Areas",
    style_function=lambda feature: {
        "fillColor": colormap(feature["properties"]["PercentShare"])
        if feature["properties"]["PercentShare"] is not None else "#cccccc",
        "color": "grey",
        "weight": 0.5,
        "fillOpacity": 0.7 if feature["properties"]["PercentShare"] is not None else 0,
    },
    tooltip=tooltip,
    highlight_function=highlight_function
)
geojson.add_to(m)

# Row layout
col_map, col_info = st.columns([3, 1])

# Render map
with col_map:
    clicked = st_folium(m, width=900, height=600)

# Info panel on the right
with col_info:
    st.markdown("### SA2 Mode Share Breakdown")

    if clicked and "last_active_drawing" in clicked:
        props = clicked["last_active_drawing"]["properties"]
        sa2_code = props["SA2_MAIN16"]
        sa2_name = props["SA2_NAME16"]
        st.markdown(f"**{sa2_name}** (Code: {sa2_code})")

        zone_df = df[df["SA2_16_CODE"] == sa2_code].copy()
        zone_df = zone_df.groupby("Mode")["Persons"].sum().reset_index()
        total_selected = zone_df[zone_df["Mode"].isin(st.session_state.selected_modes)]["Persons"].sum()
        if total_selected > 0:
            zone_df["% Share (selected total)"] = zone_df["Persons"] / total_selected * 100
        else:
            zone_df["% Share (selected total)"] = 0

        st.dataframe(zone_df.rename(columns={"Persons": "Persons (raw)"}), use_container_width=True)
    else:
        st.info("Click a zone to see detailed mode share info.")
