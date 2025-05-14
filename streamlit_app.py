import streamlit as st
import pandas as pd
import geopandas as gpd
import folium
from folium import Choropleth
from streamlit_folium import st_folium
from branca.colormap import linear

# Load data using correct paths
geojson_path = "data/sa2.geojson"
csv_path = "data/data_Mode_Census_UR_SA2.csv"

geojson_data = gpd.read_file(geojson_path)
df = pd.read_csv(csv_path)

# Sidebar filters
st.sidebar.header("Mode Selector")

all_modes = sorted(df["Mode"].unique())
select_all = st.sidebar.checkbox("Select All Modes", value=False)
selected_modes = st.sidebar.multiselect("Choose modes", all_modes, default=all_modes if select_all else [])

# Filter and process data
if selected_modes:
    filtered_data = df[df["Mode"].isin(selected_modes)].copy()

    # Calculate total persons per SA2
    total_persons = filtered_data.groupby("SA2_16_CODE")["Persons"].sum().reset_index()
    total_persons.columns = ["SA2_16_CODE", "TotalPersons"]
    filtered_data = filtered_data.merge(total_persons, on="SA2_16_CODE", how="left")
    filtered_data["Percentage"] = (filtered_data["Persons"] / filtered_data["TotalPersons"]) * 100

    # Mode for visualization
    mode_for_visual = st.sidebar.selectbox("Mode to Visualize", selected_modes)

    # Get percentage for selected visual mode
    mode_data = filtered_data[filtered_data["Mode"] == mode_for_visual]
    percentage_by_sa2 = mode_data.set_index("SA2_16_CODE")["Percentage"].to_dict()

    # Merge values into GeoDataFrame
    geojson_data["value"] = geojson_data["SA2_MAIN16"].map(percentage_by_sa2)

    # Setup map
    m = folium.Map(location=[-33.86, 151.21], zoom_start=10, tiles="cartodbpositron")
    colormap = linear.Blues_09.scale(0, max(percentage_by_sa2.values(), default=1))
    colormap.caption = f"Percentage of {mode_for_visual}"
    colormap.add_to(m)

    def style_function(feature):
        sa2_code = feature["properties"]["SA2_MAIN16"]
        pct = percentage_by_sa2.get(sa2_code, 0)
        return {
            "fillColor": colormap(pct),
            "color": "black",
            "weight": 0.3,
            "fillOpacity": 0.7,
        }

    tooltip = folium.GeoJsonTooltip(fields=["SA2_MAIN16", "SA2_NAME16"])

    folium.GeoJson(
        geojson_data,
        name="SA2",
        style_function=style_function,
        tooltip=tooltip
    ).add_to(m)

    st_data = st_folium(m, width=700, height=600)

    # Show breakdown if a zone is clicked
    if st_data and st_data.get("last_active_drawing"):
        props = st_data["last_active_drawing"]["properties"]
        clicked_code = props["SA2_MAIN16"]
        clicked_name = props["SA2_NAME16"]
        clicked_data = filtered_data[filtered_data["SA2_16_CODE"] == clicked_code]

        if not clicked_data.empty:
            clicked_data["Percentage"] = (clicked_data["Persons"] / clicked_data["TotalPersons"]) * 100
            st.write(f"Detailed Mode Share for {clicked_name} (Code: {clicked_code})")
            st.dataframe(clicked_data[["SA2_16", "Mode", "Persons", "Percentage"]].round(2))
        else:
            st.write("No data available for the selected zone.")
else:
    st.warning("Please select at least one mode.")
