# ✅ Combined NutriAI + CGM-WHOOP App
# Streamlit app merging nutriai_frontend and cgmapp functionalities
# -------------------------------------------------------

import streamlit as st
import requests
import json
import os
import openai
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import StringIO

# Setup
st.set_page_config(page_title="NutriAI + CGM Planner", layout="wide")
openai.api_key = os.getenv("OPENAI_API_KEY")

# Initialize session state
if "response" not in st.session_state:
    st.session_state.response = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_file" not in st.session_state:
    st.session_state.chat_file = None

# Navigation
page = st.sidebar.radio("Navigate", [
    "Nutrition Profile",
    "ChatGPT Meal Plan",
    "Glucose & Chat",
    "WHOOP + CGM Adjustments",
    "Insulin Resistance",
    "Glucose Trend Charts",
    "USDA Food Search"
])

# Inject NutriAI Pages
if page in ["Nutrition Profile", "ChatGPT Meal Plan", "Glucose & Chat", "USDA Food Search"]:
    # Only execute nutriai sections
    exec(nutriai_code, globals())

# Inject CGM-WHOOP Pages
elif page in ["WHOOP + CGM Adjustments", "Insulin Resistance", "Glucose Trend Charts"]:
    # Only execute relevant sections of the CGM app
    exec(cgmapp_code, globals())