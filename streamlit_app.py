import streamlit as st

st.title("🚀 Hello Streamlit!")
st.write("Welcome to your first Streamlit app.")
st.write("This app is running from a Python script.")
st.write("Try editing the code and see changes when you rerun it!")

name = st.text_input("What's your name?")
if name:
	st.success(f"Nice to meet you, {name}!")
