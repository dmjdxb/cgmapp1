import os
import streamlit as st
import requests


API_URL = os.getenv("API_URL", "https://cgmapp1.onrender.com")

 # Your FastAPI backend

# Session state to store the token
if "auth_token" not in st.session_state:
    st.session_state.auth_token = None

def signup(username, email, full_name, password):
    res = requests.post(f"{API_URL}/signup", json={
        "username": username,
        "email": email,
        "full_name": full_name,
        "password": password
    })
    
    # Debug print
    st.write("DEBUG: signup status code →", res.status_code)
    st.write("DEBUG: signup response →", res.text)

    if res.status_code == 200:
        st.success("✅ Account created. Please log in.")
    else:
        st.error(f"❌ Signup failed: {res.json()['detail']}")

    if res.status_code == 200:
        st.success("✅ Account created. Please log in.")
    else:
        st.error(f"❌ Signup failed: {res.json()['detail']}")

def login(username, password):
    res = requests.post(f"{API_URL}/token", data={
        "username": username,
        "password": password
    })
    if res.status_code == 200:
        st.session_state.auth_token = res.json()["access_token"]
        st.success("✅ Logged in!")
    else:
        st.error("❌ Login failed. Invalid username or password.")

def logout():
    st.session_state.auth_token = None

def get_profile():
    headers = {"Authorization": f"Bearer {st.session_state.auth_token}"}
    res = requests.get(f"{API_URL}/profile", headers=headers)
    if res.status_code == 200:
        return res.json()
    return None

# ─────────────────────────────
# Streamlit UI Starts Here
# ─────────────────────────────

st.title("🔐 Login Portal for Your Health App")

if not st.session_state.auth_token:
    tab1, tab2 = st.tabs(["Log In", "Sign Up"])

    with tab1:
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        if st.button("Log In"):
            login(username, password)

    with tab2:
        new_username = st.text_input("New Username")
        email = st.text_input("Email")
        full_name = st.text_input("Full Name")
        new_password = st.text_input("Create Password", type="password")
        if st.button("Create Account"):
            signup(new_username, email, full_name, new_password)
else:
    profile = get_profile()
    st.success(f"✅ Logged in as {profile['username']}")
    if st.button("Log out"):
        logout()

    st.subheader("📈 Protected CGM + WHOOP Dashboard")
    st.write("Now you can access secure app features here.")
