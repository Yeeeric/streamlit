import streamlit as st
import pandas as pd
import json
import folium
from folium import Choropleth
from streamlit_folium import st_folium
from branca.colormap import linear

# ---- Session state initialization ----
if "select_all" not in st.session_state:
    st.session_state.select_all = False
if "selected_modes" not in st.session_state:
    st.session_state.selected_modes = []

# ---- Sidebar: Year toggle ----
st.sidebar.header("Settings")
year = st.sidebar.radio("Select Year", ["2016", "2021"], key="year")

# ---- File paths based on year ----
geojson_path = f"data/{year}_SA2.geojson"
csv_path = f"data/{year}_SA2UR_Mode.csv"

# ---- Load data ----
with open(geojson_path, "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

df = pd.read_csv(csv_path, dtype={"SA2_CODE": str})

# ---- Determine correct GeoJSON keys ----
code_key = "SA2_MAIN16" if year == "2016" else "SA2_CODE21"
name_key = "SA2_NAME16" if year == "2016" else "SA2_NAME21"

# ---- Sidebar: Mode selector ----
st.sidebar.header("Mode Selector")

all_modes = sorted(df["Mode"].unique())

# Update selected modes if select all is toggled
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

    total_persons = filtered_data.groupby("SA2_CODE")["Persons"].sum().reset_index()
    total_persons.columns = ["SA2_CODE", "TotalPersons"]
    filtered_data = filtered_data.merge(total_persons, on="SA2_CODE", how="left")
    filtered_data["Percentage"] = (filtered_data["Persons"] / filtered_data["TotalPersons"]) * 100

    mode_for_visual = st.sidebar.selectbox("Mode to Visualize", selected_modes)

    mode_data = filtered_data[filtered_data["Mode"] == mode_for_visual]
    percentage_by_sa2 = mode_data.set_index("SA2_CODE")["Percentage"].to_dict()

    percentages = [v for v in percentage_by_sa2.values() if pd.notnull(v) and v >= 0]
    min_val, max_val = (min(percentages), max(percentages)) if percentages else (0, 1)
    if min_val == max_val:
        max_val += 1

    # Use dark tiles for the map
    m = folium.Map(location=[-33.86, 151.01], zoom_start=10, tiles="CartoDB dark_matter")

    # Use a color scale that stands out on dark backgrounds
    colormap = linear.YlGnBu_09.scale(min_val, max_val)
    colormap.caption = f"Percentage of {mode_for_visual}"
    colormap.add_to(m)

    def style_function(feature):
        sa2_code = feature["properties"][code_key]
        pct = percentage_by_sa2.get(sa2_code, 0)
        try:
            return {
                "fillColor": colormap(pct),
                "color": "white",          # lighter border for dark bg
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

    tooltip = folium.GeoJsonTooltip(fields=[code_key, name_key])

    folium.GeoJson(
        geojson_data,
        name="SA2",
        style_function=style_function,
        tooltip=tooltip
    ).add_to(m)

    st_data = st_folium(m, width=700, height=600)

    if st_data and st_data.get("last_active_drawing"):
        props = st_data["last_active_drawing"]["properties"]
        clicked_code = props[code_key]
        clicked_name = props[name_key]
        clicked_data = filtered_data[filtered_data["SA2_CODE"] == clicked_code]

        if not clicked_data.empty:
            clicked_data["Percentage"] = (clicked_data["Persons"] / clicked_data["TotalPersons"]) * 100
            st.markdown(f"**Detailed Mode Share for {clicked_name}**\n*(Code: {clicked_code})*")
            st.dataframe(clicked_data[["SA2", "Mode", "Persons", "Percentage"]].round(2),
                         use_container_width=True)
        else:
            st.info("No data available for the selected zone.")
else:
    st.warning("Please select at least one mode.")
