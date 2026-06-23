import streamlit as st

st.title("My First Python Web App")
name = st.text_input("What is your name?")

if st.button("Greet Me"):
    st.success(f"Hello, {name}! Welcome to your web app.")
    