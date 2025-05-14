import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
from folium import Choropleth
from branca.colormap import linear

# --- Load Data ---
geojson_path = "data/sa2.geojson"
csv_path = "data/data_Mode_Census_UR_SA2.csv"

with open(geojson_path) as f:
    geojson_data = json.load(f)

df = pd.read_csv(csv_path)

# --- Sidebar: Mode Selection ---
st.sidebar.header("Select Modes of Transport")
all_modes = df["Mode"].unique().tolist()

select_all = st.sidebar.checkbox("Select All", value=False)
selected_modes = st.sidebar.multiselect(
    "Modes", all_modes, default=all_modes if select_all else []
)

# Subset data based on selected modes
filtered_data = df[df["Mode"].isin(selected_modes)]

# --- Sidebar: Mode for Visualization ---
visual_mode = None
if selected_modes:
    visual_mode = st.sidebar.selectbox("Select mode to visualize on map", selected_modes)

# --- Calculate zone-level mode share ---
if visual_mode:
    zone_totals = (
        filtered_data.groupby("SA2_16")["Persons"]
        .sum()
        .reset_index(name="TotalPersons")
    )
    visual_data = (
        filtered_data[filtered_data["Mode"] == visual_mode]
        .groupby("SA2_16")["Persons"]
        .sum()
        .reset_index(name="VisualPersons")
    )
    zone_data = pd.merge(zone_totals, visual_data, on="SA2_16", how="left")
    zone_data["Percentage"] = (zone_data["VisualPersons"] / zone_data["TotalPersons"]) * 100
    zone_data["Percentage"] = zone_data["Percentage"].fillna(0)

    # Create a mapping from SA2_16 to percentage
    percentage_by_sa2 = zone_data.set_index("SA2_16")["Percentage"].to_dict()

    # --- Create Colormap ---
    colormap = linear.Blues_09.scale(0, max(zone_data["Percentage"]))
    colormap.caption = f"Percentage of {visual_mode} users"

    # --- Folium Map ---
    m = folium.Map(location=[-33.86, 151.21], zoom_start=10, tiles="cartodbpositron")

    def style_function(feature):
        sa2_code = feature["properties"]["SA2_16"]
        pct = percentage_by_sa2.get(sa2_code, 0)
        return {
            "fillColor": colormap(pct),
            "color": "black",
            "weight": 0.5,
            "fillOpacity": 0.7,
        }

    folium.GeoJson(
        geojson_data,
        name="SA2",
        style_function=style_function,
        tooltip=folium.GeoJsonTooltip(fields=["SA2_16", "SA2_NAME16"]),
    ).add_to(m)

    colormap.add_to(m)

    st_data = st_folium(m, width=800, height=600)

    # --- Display zone-specific data on click ---
    if st_data.get("last_active_drawing"):
        clicked_zone_code = st_data["last_active_drawing"]["properties"]["SA2_16"]
        clicked_zone_name = st_data["last_active_drawing"]["properties"]["SA2_NAME16"]
        clicked_data = filtered_data[filtered_data["SA2_16"] == clicked_zone_code]
        if not clicked_data.empty:
            clicked_data = clicked_data.copy()
            total_persons = clicked_data["Persons"].sum()
            clicked_data["Percentage"] = (clicked_data["Persons"] / total_persons) * 100
            st.sidebar.markdown(
                f"### Mode Share for {clicked_zone_name} (Code: {clicked_zone_code})"
            )
            st.sidebar.dataframe(
                clicked_data[["Mode", "Persons", "Percentage"]].sort_values(by="Percentage", ascending=False),
                use_container_width=True,
            )
        else:
            st.sidebar.write("No data available for the selected zone.")
else:
    st.write("Please select at least one mode of transport.")
