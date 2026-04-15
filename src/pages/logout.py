""" Simple no input page,

so it can be included in the sidebar for logging out, 
and then redirecting back to the login page.
"""
import streamlit as st

st.session_state.clear()
st.switch_page('pages/login.py')