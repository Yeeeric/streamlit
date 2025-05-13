import streamlit as st
import pydeck as pdk
import json

st.title("🗺️ Pydeck GeoJSON Viewer")

# Load GeoJSON
with open("data/your_file.geojson") as f:
    geojson_data = json.load(f)

layer = pdk.Layer(
    "GeoJsonLayer",
    geojson_data,
    stroked=True,
    filled=True,
    line_width_min_pixels=1,
    get_fill_color=[180, 0, 200, 40],
    get_line_color=[255, 0, 0],
)

view_state = pdk.ViewState(latitude=-33.87, longitude=151.21, zoom=10)

r = pdk.Deck(layers=[layer], initial_view_state=view_state)

st.pydeck_chart(r)
