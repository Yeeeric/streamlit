import streamlit as st
import pandas as pd
import json
import folium
from streamlit_folium import st_folium
from branca.colormap import LinearColormap

# Load spatial and tabular data
with open("data/sa2.geojson") as f:
    geojson_data = json.load(f)

df = pd.read_csv("data/data_Mode_Census_UR_SA2.csv")
df["SA2_16_CODE"] = df["SA2_16_CODE"].astype(str)

# Pivot for faster lookup
pivot_df = df.pivot_table(index="SA2_16_CODE", columns="Mode", values="Persons", aggfunc="sum", fill_value=0)

# Sidebar - Mode filter
st.sidebar.title("Mode Filter")
all_modes = sorted(df["Mode"].unique())
if "selected_modes" not in st.session_state:
    st.session_state.selected_modes = all_modes.copy()

# Select/Deselect All button
def toggle_select_all():
    if set(st.session_state.selected_modes) == set(all_modes):
        st.session_state.selected_modes = []
    else:
        st.session_state.selected_modes = all_modes.copy()

st.sidebar.button("Select/Deselect All", on_click=toggle_select_all)

# Checkbox list
selected_modes = st.sidebar.multiselect("Choose modes", all_modes, default=st.session_state.selected_modes)
st.session_state.selected_modes = selected_modes

# Compute mode share
if selected_modes:
    pivot_df["Selected_Total"] = pivot_df[selected_modes].sum(axis=1)
    pivot_df["Selected_Share"] = pivot_df["Selected_Total"] / pivot_df["Selected_Total"].sum() * 100
else:
    pivot_df["Selected_Total"] = 0
    pivot_df["Selected_Share"] = 0

# Map setup
m = folium.Map(location=[-33.87, 151.05], zoom_start=10, control_scale=True, tiles="cartodbpositron")

# Color scale
max_val = pivot_df["Selected_Share"].max()
colormap = LinearColormap(colors=["#e5f5e0", "#31a354"], vmin=0, vmax=max_val)
colormap.caption = "Selected Mode Share (%)"
colormap.add_to(m)

# Attach mode share to geojson features
for feature in geojson_data["features"]:
    sa2_code = str(feature["properties"]["SA2_MAIN16"])
    value = pivot_df.loc[sa2_code, "Selected_Share"] if sa2_code in pivot_df.index else None
    feature["properties"]["mode_share"] = value

    # Store raw values as well
    if sa2_code in pivot_df.index:
        for mode in selected_modes:
            feature["properties"][f"mode_{mode}"] = pivot_df.loc[sa2_code, mode]
        feature["properties"]["selected_total"] = pivot_df.loc[sa2_code, "Selected_Total"]

# Define styling
def style_function(feature):
    share = feature["properties"]["mode_share"]
    return {
        "fillOpacity": 0.7 if share is not None else 0,
        "weight": 0.3,
        "color": "black",
        "fillColor": colormap(share) if share is not None else "transparent",
    }

# Add choropleth
geojson_layer = folium.GeoJson(
    geojson_data,
    name="Mode Share",
    style_function=style_function,
    tooltip=folium.GeoJsonTooltip(
        fields=["SA2_NAME16", "mode_share"],
        aliases=["SA2", "Selected Share (%)"],
        localize=True,
        labels=True,
        sticky=False,
        toLocaleString=True,
        style=("background-color: white; color: #333; font-size: 12px; padding: 5px;"),
    ),
)

geojson_layer.add_to(m)

# Display map and capture click
st_data = st_folium(m, width=1000, height=600)

# Show clicked feature info
if st_data and st_data.get("last_active_drawing", None):
    sa2_code_clicked = st_data["last_active_drawing"]["properties"]["SA2_MAIN16"]
    sa2_name = st_data["last_active_drawing"]["properties"]["SA2_NAME16"]

    st.markdown(f"### Mode Share for {sa2_name}")
    if sa2_code_clicked in pivot_df.index:
        clicked_row = pivot_df.loc[sa2_code_clicked]
        total = clicked_row[selected_modes].sum()
        table_data = {
            "Mode": [],
            "Persons": [],
            "Share (%)": []
        }
        for mode in selected_modes:
            count = clicked_row[mode]
            share = (count / total * 100) if total > 0 else 0
            table_data["Mode"].append(mode)
            table_data["Persons"].append(int(count))
            table_data["Share (%)"].append(round(share, 2))

        breakdown_df = pd.DataFrame(table_data)
        st.dataframe(breakdown_df, use_container_width=True)
    else:
        st.info("No data available for this SA2.")
