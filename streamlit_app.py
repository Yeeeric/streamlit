import streamlit as st
import pandas as pd
import json
from keplergl import KeplerGl
from streamlit_keplergl import keplergl_static

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

# ---- Main processing and Kepler map generation ----
if selected_modes:
    filtered_data = df[df["Mode"].isin(selected_modes)].copy()

    total_persons = filtered_data.groupby("SA2_CODE")["Persons"].sum().reset_index()
    total_persons.columns = ["SA2_CODE", "TotalPersons"]
    filtered_data = filtered_data.merge(total_persons, on="SA2_CODE", how="left")
    filtered_data["Percentage"] = (filtered_data["Persons"] / filtered_data["TotalPersons"]) * 100

    mode_for_visual = st.sidebar.selectbox("Mode to Visualize", selected_modes)

    # Aggregate percentage for selected mode
    mode_data = filtered_data[filtered_data["Mode"] == mode_for_visual]
    percentage_by_sa2 = mode_data.set_index("SA2_CODE")["Percentage"].to_dict()

    # Add percentage to geojson properties
    for feature in geojson_data["features"]:
        sa2_code = feature["properties"][code_key]
        feature["properties"]["Percentage"] = round(percentage_by_sa2.get(sa2_code, 0), 2)

    # Create and show Kepler.gl map
    kepler_map = KeplerGl(height=600)
    kepler_map.add_data(data=geojson_data, name="SA2 Mode Share")
    keplergl_static(kepler_map)

    # Handle clicks (Kepler doesn’t support built-in click-to-filter)
    st.markdown("Use the Kepler interface to explore data interactively.")

else:
    st.warning("Please select at least one mode.")
