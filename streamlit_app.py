# streamlit_app.py

import streamlit as st
import pandas as pd
import numpy as np

st.title("Random Points on a Map - Sydney Example")

# Generate some random latitude and longitude data around Sydney
# Sydney's approximate coordinates: -33.8688, 151.2093
num_points = st.slider("Number of points", 1, 100, 10)

lat = -33.8688 + np.random.randn(num_points) * 0.01
lon = 151.2093 + np.random.randn(num_points) * 0.01

data = pd.DataFrame({
    'lat': lat,
    'lon': lon
})

st.map(data)

st.write("These are randomly generated points near Sydney.")
