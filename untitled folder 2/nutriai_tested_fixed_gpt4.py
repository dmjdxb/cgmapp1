import streamlit as st
import openai
import requests
import json
import os
import pandas as pd
import plotly.express as px
from datetime import datetime
from io import StringIO

st.set_page_config(page_title="NutriAI + CGM Planner", layout="wide")

# ✅ Corrected OpenAI client initialization
client = openai.OpenAI(api_key="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")

# ✅ Initialize session state
if "response" not in st.session_state:
    st.session_state.response = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_file" not in st.session_state:
    st.session_state.chat_file = None

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", [
    "Welcome", "Meal Plan Test"
])

if page == "Welcome":
    st.title("🚀 NutriAI + CGM App")
    st.write("You're connected to OpenAI GPT-4 with hardcoded API key.")
    st.success("✅ OpenAI Client Initialized Successfully")

elif page == "Meal Plan Test":
    st.title("🍽️ WHOOP + CGM Meal Plan Test")
    prompt = "Create a 1-day meal plan for 2200 kcal, 180g carbs, 150g protein, 65g fat for athletic recovery."

    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a sports dietitian."},
                {"role": "user", "content": prompt}
            ]
        )
        meal_plan = response.choices[0].message.content
        st.text_area("Meal Plan Output", meal_plan, height=300)
    except Exception as e:
        st.error(f"❌ GPT-4 Error: {e}")