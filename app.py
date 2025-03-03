import streamlit as st

st.set_page_config(
    page_title="Data Analysis Assistant",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Configure Streamlit to listen on all interfaces
import os
os.environ['STREAMLIT_SERVER_ADDRESS'] = '0.0.0.0'
os.environ['STREAMLIT_SERVER_PORT'] = '8501'

st.header('Welcome to Streamlit!')
