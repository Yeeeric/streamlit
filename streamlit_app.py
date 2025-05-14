import streamlit as st
import pandas as pd
import json
import folium
from folium import Choropleth
from streamlit_folium import st_folium
from branca.colormap import linear

# Load data
geojson_path = "data/2016_SA2.geojson"
csv_path = "data/2016_SA2UR_Mode.csv"

with open(geojson_path, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

df = pd.read_csv(csv_path, dtype={"SA2_CODE": str})

# Sidebar filters
st.sidebar.header("Mode Selector")

all_modes = sorted(df["Mode"].unique())
select_all = st.sidebar.checkbox("Select All Modes", value=False)
selected_modes = st.sidebar.multiselect("Choose modes", all_modes, default=all_modes if select_all else [])

# Filter and process data
if selected_modes:
    filtered_data = df[df["Mode"].isin(selected_modes)].copy()

    # Calculate total persons per SA2
    total_persons = filtered_data.groupby("SA2_CODE")["Persons"].sum().reset_index()
    total_persons.columns = ["SA2_CODE", "TotalPersons"]
    filtered_data = filtered_data.merge(total_persons, on="SA2_CODE", how="left")
    filtered_data["Percentage"] = (filtered_data["Persons"] / filtered_data["TotalPersons"]) * 100

    # Mode for visualization
    mode_for_visual = st.sidebar.selectbox("Mode to Visualize", selected_modes)

    # Get percentage for selected visual mode
    mode_data = filtered_data[filtered_data["Mode"] == mode_for_visual]
    percentage_by_sa2 = mode_data.set_index("SA2_CODE")["Percentage"].to_dict()

    # Filter out invalid values
    percentages = [v for v in percentage_by_sa2.values() if pd.notnull(v) and v >= 0]

    if percentages:
        min_val = min(percentages)
        max_val = max(percentages)
        if min_val == max_val:
            max_val += 1  # Avoid zero range
    else:
        min_val, max_val = 0, 1

    # Setup map
    m = folium.Map(location=[-33.86, 151.01], zoom_start=10, tiles="cartodbpositron")
    colormap = linear.Blues_09.scale(min_val, max_val)
    colormap.caption = f"Percentage of {mode_for_visual}"
    colormap.add_to(m)

    def style_function(feature):
        sa2_code = feature["properties"]["SA2_MAIN16"]
        pct = percentage_by_sa2.get(sa2_code, 0)
        try:
            return {
                "fillColor": colormap(pct),
                "color": "black",
                "weight": 0.3,
                "fillOpacity": 0.7,
            }
        except ValueError:
            return {
                "fillColor": "#cccccc",
                "color": "black",
                "weight": 0.3,
                "fillOpacity": 0.3,
            }

    tooltip = folium.GeoJsonTooltip(fields=["SA2_MAIN16", "SA2_NAME16"])

    folium.GeoJson(
        geojson_data,
        name="SA2",
        style_function=style_function,
        tooltip=tooltip
    ).add_to(m)

    col1, col2 = st.columns([2, 1])  # Wider map, narrower table

    with col1:
        st_data = st_folium(m, width=700, height=600)

    with col2:
        if st_data and st_data.get("last_active_drawing"):
            props = st_data["last_active_drawing"]["properties"]
            clicked_code = props["SA2_MAIN16"]
            clicked_name = props["SA2_NAME16"]
            clicked_data = filtered_data[filtered_data["SA2_CODE"] == clicked_code]

            if not clicked_data.empty:
                clicked_data["Percentage"] = (clicked_data["Persons"] / clicked_data["TotalPersons"]) * 100
                st.markdown(f"**Detailed Mode Share for {clicked_name}**  
                             *(Code: {clicked_code})*")
                st.dataframe(clicked_data[["SA2", "Mode", "Persons", "Percentage"]].round(2),
                             use_container_width=True)
            else:
                st.info("No data available for the selected zone.")

else:
    st.warning("Please select at least one mode.")
