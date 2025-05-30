import streamlit as st
import pandas as pd
import json
import folium
from folium import Choropleth
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

# ---- Session state initialization ----
if "select_all" not in st.session_state:
    st.session_state.select_all = False
if "selected_modes" not in st.session_state:
    st.session_state.selected_modes = []

# ---- Sidebar: Geography and Year toggle ----
st.sidebar.header("Settings")
geo_level = st.sidebar.radio("Select Geography Level", ["SA2", "DZN"], key="geo_level")
year = st.sidebar.radio("Select Year", ["2016", "2021"], key="year")

# ---- File paths based on year and geography ----
geojson_path = f"data/{year}_{geo_level}.geojson"

csv_file_map = {
    ("2016", "SA2"): "data/2016_SA2UR_Mode.csv",
    ("2021", "SA2"): "data/2021_SA2UR_Mode.csv",
    ("2016", "DZN"): "data/2016_DZNPOW_Mode.csv",
    ("2021", "DZN"): "data/2021_DZNPOW_Mode.csv",
}

csv_path = csv_file_map[(year, geo_level)]

# ---- Load GeoJSON ----
with open(geojson_path, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# ---- Determine zone code column for CSV ----
code_column = "SA2_CODE" if geo_level == "SA2" else "DZN"
df = pd.read_csv(csv_path, dtype={code_column: str})

# ---- Determine correct GeoJSON keys ----
if geo_level == "SA2":
    code_key = "SA2_MAIN16" if year == "2016" else "SA2_CODE21"
    name_key = "SA2_NAME16" if year == "2016" else "SA2_NAME21"
else:
    code_key = "DZN_CODE16" if year == "2016" else "DZN_CODE21"
    name_key = code_key  # No name field for DZN, fallback to code

# ---- Sidebar: Mode selector ----
st.sidebar.header("Mode Selector")
all_modes = sorted(df["Mode"].unique())

# Update selected modes if "Select All" is toggled
if st.sidebar.checkbox("Select All Modes", value=st.session_state.select_all, key="select_all_checkbox"):
    st.session_state.selected_modes = all_modes
    st.session_state.select_all = True
else:
    st.session_state.select_all = False

# Manual checkbox selection for each mode
selected_modes = []
st.sidebar.write("Choose modes:")
for mode in all_modes:
    if mode not in st.session_state:
        st.session_state[mode] = mode in st.session_state.selected_modes

    checked = st.sidebar.checkbox(mode, value=st.session_state[mode], key=f"chk_{mode}")
    if checked:
        selected_modes.append(mode)
    st.session_state[mode] = checked

# Update session state
st.session_state.selected_modes = selected_modes

# ---- Main processing and map generation ----
if selected_modes:
    filtered_data = df[df["Mode"].isin(selected_modes)].copy()

    total_persons = filtered_data.groupby(code_column)["Persons"].sum().reset_index()
    total_persons.columns = [code_column, "TotalPersons"]
    filtered_data = filtered_data.merge(total_persons, on=code_column, how="left")
    filtered_data["Percentage"] = (filtered_data["Persons"] / filtered_data["TotalPersons"]) * 100

    mode_for_visual = st.sidebar.selectbox("Mode to Visualize", selected_modes)

    mode_data = filtered_data[filtered_data["Mode"] == mode_for_visual]
    percentage_by_zone = mode_data.set_index(code_column)["Percentage"].to_dict()

    percentages = [v for v in percentage_by_zone.values() if pd.notnull(v) and v >= 0]
    min_val, max_val = (min(percentages), max(percentages)) if percentages else (0, 1)
    if min_val == max_val:
        max_val += 1

    # Map configuration
    m = folium.Map(location=[-33.86, 151.01], zoom_start=10, tiles="CartoDB dark_matter")

    # Custom Inferno-like colormap
    colormap = LinearColormap(
        colors=["#000004", "#420a68", "#932667", "#dd513a", "#fca50a", "#fcffa4"],
        vmin=min_val,
        vmax=max_val
    )
    colormap.caption = f"Percentage of {mode_for_visual}"
    colormap.add_to(m)

    def style_function(feature):
        zone_code = feature["properties"][code_key]
        pct = percentage_by_zone.get(zone_code, 0)
        try:
            return {
                "fillColor": colormap(pct),
                "color": "white",
                "weight": 0.5,
                "fillOpacity": 0.7,
            }
        except ValueError:
            return {
                "fillColor": "#444444",
                "color": "white",
                "weight": 0.5,
                "fillOpacity": 0.3,
            }

    tooltip_fields = [code_key] if geo_level == "DZN" else [code_key, name_key]
    tooltip = folium.GeoJsonTooltip(fields=tooltip_fields)

    folium.GeoJson(
        geojson_data,
        name=geo_level,
        style_function=style_function,
        tooltip=tooltip
    ).add_to(m)

    st_data = st_folium(m, width=700, height=600)

    if st_data and st_data.get("last_active_drawing"):
        props = st_data["last_active_drawing"]["properties"]
        clicked_code = props[code_key]
        clicked_name = props.get(name_key, clicked_code)
        clicked_data = filtered_data[filtered_data[code_column] == clicked_code]

        if not clicked_data.empty:
            clicked_data["Percentage"] = (clicked_data["Persons"] / clicked_data["TotalPersons"]) * 100
            st.markdown(f"**Detailed Mode Share for {clicked_name}**\n*(Code: {clicked_code})*")
            st.dataframe(clicked_data[[code_column, "Mode", "Persons", "Percentage"]].round(2),
                         use_container_width=True)
        else:
            st.info("No data available for the selected zone.")
else:
    st.warning("Please select at least one mode.")
