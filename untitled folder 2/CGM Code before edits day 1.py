# ✅ Fully Merged NutriAI + CGM-WHOOP App
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

def refresh_whoop_token(user_id):
    import requests
    import datetime

    token_doc = st.session_state.db.collection("users").document(user_id).collection("whoop_auth").document("token").get()
    if not token_doc.exists:
        return {"error": "No WHOOP token found for user."}

    token_data = token_doc.to_dict()
    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        return {"error": "Refresh token missing."}

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": st.secrets["WHOOP_CLIENT_ID"],
        "client_secret": st.secrets["WHOOP_CLIENT_SECRET"]
    }

    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    response = requests.post("https://api.prod.whoop.com/oauth/oauth2/token", data=payload, headers=headers)

    if response.status_code == 200:
        new_token_data = response.json()
        access_token = new_token_data["access_token"]
        new_refresh_token = new_token_data.get("refresh_token", refresh_token)
        expires_in = new_token_data["expires_in"]

        st.session_state.db.collection("users").document(user_id).collection("whoop_auth").document("token").set({
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "expires_in": expires_in,
            "timestamp": datetime.datetime.utcnow().isoformat()
        })

        return {
            "status": "success",
            "access_token": access_token,
            "expires_in": expires_in
        }
    else:
        return {
            "error": "Failed to refresh token",
            "status_code": response.status_code,
            "details": response.text
        }

import firebase_admin
from firebase_admin import credentials, firestore

if "firebase" not in st.session_state:
    if not firebase_admin._apps:
        cred = credentials.Certificate({
            "type": "service_account",
            "project_id": st.secrets["firebase_project_id"],
            "private_key_id": st.secrets["firebase_private_key_id"],
            "private_key": st.secrets["firebase_private_key"].replace("\\n", "\n"),
            "client_email": st.secrets["firebase_client_email"],
            "client_id": st.secrets["firebase_client_id"],
            "auth_uri": st.secrets["firebase_auth_uri"],
            "token_uri": st.secrets["firebase_token_uri"],
            "auth_provider_x509_cert_url": st.secrets["firebase_auth_provider_x509_cert_url"],
            "client_x509_cert_url": st.secrets["firebase_client_x509_cert_url"]
        })
        firebase_admin.initialize_app(cred)
    st.session_state.db = firestore.client()

st.set_page_config(page_title="NutriAI + CGM Planner", layout="wide")

# ✅ Verified GPT-4 client setup with working key

client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])



# Initialize session state
if "response" not in st.session_state:
    st.session_state.response = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_file" not in st.session_state:
    st.session_state.chat_file = None

# Sidebar Navigation
page = st.sidebar.radio("Navigate", [
    "Nutrition Profile",
    "NutriAI Meal Plan",
    "Glucose & Chat",
    "WHOOP + CGM Adjustments",
    "Insulin Resistance",
    "Glucose Trend Charts",
    "User Dashboard",
    "Connect WHOOP"
])

# ========== PAGE 1: Nutrition Profile ==========
if page == "Nutrition Profile":
    st.title("📋 Build Your Nutrition Profile")

    with st.form("profile_form"):
        st.subheader("Personal Information")
        sex = st.selectbox("Sex", ["Male", "Female"])
        age = st.number_input("Age", min_value=10, max_value=100, value=30)
        height = st.number_input("Height (cm)", min_value=120, max_value=250, value=175)
        weight = st.number_input("Weight (kg)", min_value=30, max_value=200, value=75)

        st.subheader("Lifestyle & Goals")
        activity = st.selectbox("Activity Level", [
            "Sedentary (little/no exercise)",
            "Lightly active (1-3 days/week)",
            "Moderately active (3-5 days/week)",
            "Very active (6-7 days/week)",
            "Extra active (athlete or 2x/day)"
        ])
        goal = st.selectbox("Goal", ["Cut (fat loss)", "Maintain", "Gain (muscle gain)"])

        st.subheader("Diet Type")
        diet_type = st.selectbox("Select Diet Type", [
            "Balanced", "Low Carb", "Keto", "High Carb", "Carnivore",
            "Vegetarian", "Vegan", "Paleo", "Mediterranean"
        ])

        submitted = st.form_submit_button("Calculate Plan")

    if submitted:
        if sex == "Male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161

        activity_map = {
            "Sedentary (little/no exercise)": 1.2,
            "Lightly active (1-3 days/week)": 1.375,
            "Moderately active (3-5 days/week)": 1.55,
            "Very active (6-7 days/week)": 1.725,
            "Extra active (athlete or 2x/day)": 1.9
        }
        tdee = bmr * activity_map[activity]

        if "Cut" in goal:
            calories = tdee * 0.85
        elif "Gain" in goal:
            calories = tdee * 1.15
        else:
            calories = tdee

        protein_g = round(2.2 * weight)
        protein_kcal = protein_g * 4

        if diet_type == "Keto":
            carbs_g = round(0.5 * weight)
        elif diet_type == "Low Carb":
            carbs_g = round(1.0 * weight)
        elif diet_type == "High Carb":
            carbs_g = round(3.0 * weight)
        elif diet_type == "Carnivore":
            carbs_g = 0
        else:
            carbs_g = round(2.0 * weight)

        carbs_kcal = carbs_g * 4
        fat_kcal = calories - (protein_kcal + carbs_kcal)
        fat_g = round(fat_kcal / 9)

        st.session_state.diet_type = diet_type
        st.session_state.protein_g = protein_g
        st.session_state.carbs_g = carbs_g
        st.session_state.fat_g = fat_g

        st.success("✅ Personalized Daily Nutrition Plan")
        st.metric("Calories/day", round(calories))
        st.write("**Macros:**")
        st.write(f"- Protein: {protein_g}g")
        st.write(f"- Carbs: {carbs_g}g")
        st.write(f"- Fat: {fat_g}g")

# ========== Other Pages Will Be Inserted Here ==========
# (To keep file size manageable per cell, the rest will be continued)
# ================ Connect Whoop =======================#


elif page == "Connect WHOOP":
    from urllib.parse import urlencode

    st.title("🔗 Connect Your WHOOP Account")

    CLIENT_ID = st.secrets["WHOOP_CLIENT_ID"]
    CLIENT_SECRET = st.secrets["WHOOP_CLIENT_SECRET"]
    REDIRECT_URI = "https://cgmapp1py-cke3lbga3zvnszbci6gegb.streamlit.app/callback"
    TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"

    # Step 1: WHOOP Login Button
    login_params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": "read:profile read:recovery read:sleep read:cycles read:workout read:body_measurement",
        "state": "secure123"
    }

    login_url = f"https://api.prod.whoop.com/oauth/oauth2/auth?{urlencode(login_params)}"
    st.markdown(f"[👉 Click here to connect your WHOOP account]({login_url})", unsafe_allow_html=True)

    # Step 2: Handle OAuth Redirect
    query_params = st.query_params

    if "code" in query_params:
        code = query_params["code"]
        st.success("✅ Authorization code received from WHOOP!")

        user_id = st.text_input("Enter your App User ID", "")

        if user_id and st.button("Save WHOOP Token"):
            token_data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": REDIRECT_URI,
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET
            }

            headers = {"Content-Type": "application/x-www-form-urlencoded"}

            try:
                response = requests.post(TOKEN_URL, data=token_data, headers=headers)
                if response.status_code == 200:
                    tokens = response.json()
                    access_token = tokens["access_token"]
                    refresh_token = tokens.get("refresh_token", "")
                    expires_in = tokens.get("expires_in")

                    # ✅ Save to Firebase
                    st.session_state.db.collection("users").document(user_id).collection("whoop_auth").document("token").set({
                        "access_token": access_token,
                        "refresh_token": refresh_token,
                        "expires_in": expires_in,
                        "timestamp": datetime.utcnow().isoformat()
                    })

                    st.success("🎉 WHOOP token saved to Firebase successfully!")

                    # ✅ Clear ?code= from URL
                    st.query_params.clear()
                    st.rerun()
                else:
                    st.error(f"❌ Token exchange failed: {response.text}")
            except Exception as e:
                st.error(f"❌ WHOOP error: {e}")
    else:
        st.info("Click the link above to authorize WHOOP. After login, you'll return here.")



# ========== PAGE 2: ChatGPT Meal Plan ==========
elif page == "NutriAI Meal Plan":
    st.title("🥗 Generate a Sample Meal Plan Using NutriAI")


    with st.form("meal_form_chatgpt"):
        generate_chatgpt = st.form_submit_button("Generate a Meal Plan using NutriAI")

    if generate_chatgpt:
        st.markdown("### 🍽 Example Day Based on Your Macros")

        protein_g = st.session_state.get("protein_g", 0)
        carbs_g = st.session_state.get("carbs_g", 0)
        fat_g = st.session_state.get("fat_g", 0)
        diet_choice = st.session_state.get("diet_type", "Balanced")

        prompt = f"""I need a daily meal plan for a {diet_choice} diet with the following macros:
        Protein: {protein_g}g
        Carbs: {carbs_g}g
        Fat: {fat_g}g
        Provide 4 meals for the day, including breakfast, lunch, dinner, and a snack."""

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a sports dietitian that builds daily meal plans based on macros."},
                    {"role": "user", "content": prompt}
                ]
            )
            meal_plan = response.choices[0].message.content.strip()
            st.text_area("📋 NutriAI Meal Plan", meal_plan, height=300)

            user_id = st.text_input("User ID", "anonymous_user")
            if st.button("💾 Save Meal Plan to Firebase"):
                st.session_state.db.collection("users").document(user_id).collection("meal_plans").add({
                    "timestamp": firestore.SERVER_TIMESTAMP,
                    "protein_g": protein_g,
                    "carbs_g": carbs_g,
                    "fat_g": fat_g,
                    "diet_type": diet_choice,
                    "meal_plan": meal_plan
                })
                st.success("Meal plan saved to Firebase!")


        except Exception as e:
            st.error(f"Error generating meal plan with ChatGPT: {str(e)}")

            

# ========== PAGE 3: Glucose & Chat ==========
# ========== PAGE 3: Glucose & Chat ==========
elif page == "Glucose & Chat":
    st.title("📊 Glucose Monitoring & GPT Chat")

    glucose_data = st.text_area("Enter CGM values (comma-separated)", "110,115,120,108,95")
    glucose_values = [int(x.strip()) for x in glucose_data.split(",") if x.strip().isdigit()]

    if glucose_values:
        avg = sum(glucose_values) / len(glucose_values)
        min_val = min(glucose_values)
        max_val = max(glucose_values)
        st.metric("Avg Glucose", f"{avg:.1f} mg/dL")
        st.metric("Min Glucose", f"{min_val} mg/dL")
        st.metric("Max Glucose", f"{max_val} mg/dL")

        df = pd.DataFrame({
            "Reading #": [f"{i+1}" for i in range(len(glucose_values))],
            "Glucose": glucose_values
        })
        fig = px.line(df, x="Reading #", y="Glucose", markers=True, title="Glucose Trend")
        st.plotly_chart(fig)

    # Optional GPT chat
    st.subheader("💬 Ask NutriAI About Your Glucose")
    user_query = st.text_input("Ask a question (e.g. Why is my glucose high?)")

    if user_query:
        try:
            prompt = f"""My glucose readings are: {glucose_values}.
            Question: {user_query}
            Provide a brief analysis as a sports health coach."""
            
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a sports nutritionist and health coach."},
                    {"role": "user", "content": prompt}
                ]
            )
            answer = response.choices[0].message.content
            st.markdown("**NutriAI Answer:**")
            st.write(answer)
        except Exception as e:
            st.error(f"Error generating response: {e}")

elif page == "WHOOP + CGM Adjustments":
    st.title("💪 WHOOP + CGM Adaptive Nutrition Engine")

    app_user_id = st.text_input("Enter your App User ID to load WHOOP data", "")

    if app_user_id:
        doc = st.session_state.db.collection("users").document(app_user_id).collection("whoop_auth").document("token").get()
        if doc.exists:
            try:
                data = doc.to_dict()
                from datetime import datetime, timedelta

                access_token = data["access_token"]
                timestamp = data.get("timestamp")
                expires_in = data.get("expires_in")

                if timestamp:
                    token_time = datetime.fromisoformat(timestamp)
                    age = datetime.utcnow() - token_time
                    if age > timedelta(seconds=int(expires_in) - 300):
                        refresh_result = refresh_whoop_token(app_user_id)
                        if "access_token" in refresh_result:
                            access_token = refresh_result["access_token"]
                        else:
                            raise ValueError("Token refresh failed before data fetch.")

                headers = {"Authorization": f"Bearer {access_token}"}
                # 🔍 Test WHOOP Profile API to verify token is valid
                profile_resp = requests.get("https://api.prod.whoop.com/v2/user", headers=headers)
                st.write("Profile test:", profile_resp.status_code, profile_resp.text[:200])  # Optional: remove in production

                recovery_resp = requests.get("https://api.prod.whoop.com/v1/recovery", headers=headers)
                strain_resp   = requests.get("https://api.prod.whoop.com/v1/cycles", headers=headers)
                sleep_resp    = requests.get("https://api.prod.whoop.com/v1/sleep", headers=headers)


                # Debug output
                st.write("Recovery status:", recovery_resp.status_code, recovery_resp.text[:200])
                st.write("Strain status:", strain_resp.status_code, strain_resp.text[:200])
                st.write("Sleep status:", sleep_resp.status_code, sleep_resp.text[:200])


                if (
                    recovery_resp.status_code == 200 and 
                    strain_resp.status_code == 200 and 
                    sleep_resp.status_code == 200
                ):
                    recovery_data = recovery_resp.json()
                    strain_data = strain_resp.json()
                    sleep_data = sleep_resp.json()

                    if (
                        "records" in recovery_data and recovery_data["records"] and
                        "records" in strain_data and strain_data["records"] and
                        "records" in sleep_data and sleep_data["records"]
                    ):
                        latest_recovery = recovery_data["records"][0]
                        latest_strain = strain_data["records"][0]
                        latest_sleep = sleep_data["records"][0]

                        strain = round(latest_strain.get("strain", 12))
                        recovery = round(latest_recovery.get("score", 65))
                        sleep_minutes = latest_sleep.get("time_in_bed", 450)
                        sleep_hours = round(sleep_minutes / 60, 1)

                        st.metric("Strain", strain)
                        st.metric("Recovery", recovery)
                        st.metric("Sleep (hrs)", sleep_hours)

                        st.success("✅ WHOOP data loaded and applied.")
                    else:
                        raise ValueError("No WHOOP records found in one or more data types.")
                else:
                    raise ValueError("Failed to fetch WHOOP API data.")
            except Exception as e:
                st.warning(f"WHOOP error: {e}")
                st.warning("Using manual input sliders instead.")
                strain = st.slider("Strain", 0, 21, 12)
                recovery = st.slider("Recovery", 0, 100, 65)
                sleep_hours = st.slider("Sleep", 0.0, 12.0, 7.5, 0.5)
        else:
            st.warning("No WHOOP token found. Using manual input sliders.")
            strain = st.slider("Strain", 0, 21, 12)
            recovery = st.slider("Recovery", 0, 100, 65)
            sleep_hours = st.slider("Sleep", 0.0, 12.0, 7.5, 0.5)
    else:
        st.info("Enter your App User ID or use manual sliders.")
        strain = st.slider("Strain", 0, 21, 12)
        recovery = st.slider("Recovery", 0, 100, 65)
        sleep_hours = st.slider("Sleep", 0.0, 12.0, 7.5, 0.5)

    # Rest of the logic (CGM adjustments, adaptive macros...) remains here.


    # ✅ Continue with your adaptive macro engine using strain, recovery, sleep_hours


    # ✅ Keep the rest of your CGM + macro logic here


    cgm_data = st.text_area("Enter CGM values (comma-separated)", "110,115,120,108,95")
    cgm_values = [int(x.strip()) for x in cgm_data.split(",") if x.strip().isdigit()]

    base_cals = st.session_state.get("calories", 2200)
    base_prot = st.session_state.get("protein_g", 150)
    base_carbs = st.session_state.get("carbs_g", 180)
    base_fat = st.session_state.get("fat_g", 60)

    def combined_adaptive_macros(glucose_data, strain, recovery, sleep, base_cals, base_prot, base_carbs, base_fat):
        if not glucose_data:
            return base_cals, base_prot, base_carbs, base_fat

        avg_glucose = sum(glucose_data) / len(glucose_data)
        variability = max(glucose_data) - min(glucose_data)

        c_mult = 1.0
        p_mult = 1.0
        carb_mult = 1.0
        fat_mult = 1.0

        if avg_glucose > 125:
            carb_mult *= 0.85
            fat_mult *= 1.1
        elif avg_glucose < 90:
            carb_mult *= 1.1

        if variability > 40:
            c_mult *= 0.95
            carb_mult *= 0.9

        if strain > 16:
            c_mult *= 1.10
            carb_mult *= 1.15
        elif strain < 8:
            c_mult *= 0.95

        if recovery < 40:
            p_mult *= 1.05
            c_mult *= 0.95

        if sleep < 6:
            fat_mult *= 1.1
            carb_mult *= 0.9

        new_cals = base_cals * c_mult
        new_prot = base_prot * p_mult
        new_carbs = base_carbs * carb_mult
        new_fat = base_fat * fat_mult

        return int(new_cals), int(new_prot), int(new_carbs), int(new_fat)

    if cgm_values:
        w_cals, w_protein, w_carbs, w_fat = combined_adaptive_macros(
            cgm_values, strain, recovery, sleep_hours,
            base_cals, base_prot, base_carbs, base_fat
        )

        st.markdown(f"**Adaptive Calories:** {w_cals} kcal")
        st.markdown(f"**Protein:** {w_protein}g | Carbs: {w_carbs}g | Fat: {w_fat}g")

        if st.button("Generate WHOOP + CGM Meal Plan"):
            prompt = (
                f"Create a 1-day performance meal plan using {w_cals} kcal, "
                f"{w_protein}g protein, {w_carbs}g carbs, {w_fat}g fat. "
                f"User had {sleep_hours} hours sleep, strain score {strain}, and recovery score {recovery}. "
                f"Glucose values: {cgm_values}. Adjust for blood sugar balance and performance."
            )
            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a high-performance nutritionist."},
                        {"role": "user", "content": prompt}
                    ]
                )
                ai_combo_plan = response.choices[0].message.content
                st.text_area("WHOOP + CGM-Based Meal Plan", ai_combo_plan, height=300)
            except Exception as e:
                st.error("Meal plan failed: " + str(e))

# ========== PAGE 5: Insulin Resistance ==========
elif page == "Insulin Resistance":
    st.title("🧪 Insulin Resistance Monitoring")

    fasting_data = st.text_area("Enter daily fasting glucose values (comma-separated)", "95,98,105,100,99,101,107")
    postmeal_data = st.text_area("Enter daily post-meal glucose values (comma-separated)", "130,145,160,155,140,150,165")

    monitor_days = st.slider("Select monitoring period (days)", min_value=3, max_value=14, value=7)

    try:
        fasting_values = [int(x.strip()) for x in fasting_data.split(",") if x.strip().isdigit()][:monitor_days]
        postmeal_values = [int(x.strip()) for x in postmeal_data.split(",") if x.strip().isdigit()][:monitor_days]
    except:
        fasting_values = []
        postmeal_values = []

    if fasting_values and postmeal_values and len(fasting_values) == len(postmeal_values):
        dates = [f"Day {i+1}" for i in range(len(fasting_values))]
        df_glucose = pd.DataFrame({
            "Day": dates,
            "Fasting": fasting_values,
            "Post-Meal": postmeal_values
        })

        st.line_chart(df_glucose.set_index("Day"))

        avg_fasting = sum(fasting_values) / len(fasting_values)
        avg_postmeal = sum(postmeal_values) / len(postmeal_values)

        st.markdown(f"**Average Fasting Glucose:** {avg_fasting:.1f} mg/dL")
        st.markdown(f"**Average Post-Meal Glucose:** {avg_postmeal:.1f} mg/dL")

        if avg_fasting >= 100 and avg_postmeal >= 140:
            st.error("⚠️ High likelihood of insulin resistance.")
        elif avg_fasting >= 95 or avg_postmeal >= 135:
            st.warning("🟡 Early insulin resistance risk. Monitor your diet.")
        else:
            st.success("🟢 Glucose levels are within normal range.")
    else:
        st.info("Please enter equal-length data sets.")

# ========== PAGE 6: Glucose Trend Charts ==========
elif page == "Glucose Trend Charts":
    st.title("📈 Glucose Trend Visualization")

    cgm_data = st.text_area("Enter CGM values (comma-separated)", "110,115,120,108,95")
    cgm_values = [int(x.strip()) for x in cgm_data.split(",") if x.strip().isdigit()]
    if cgm_values:
        df = pd.DataFrame({
            "Day": [f"Day {i+1}" for i in range(len(cgm_values))],
            "Glucose": cgm_values
        })
        fig = px.line(df, x="Day", y="Glucose", markers=True, title="Glucose Readings Over Time")
        st.plotly_chart(fig)

elif page == "User Dashboard":
    st.title("📂 User Meal Plan History")

    user_id = st.text_input("Enter User ID to load history", "")
    if user_id:
        try:
            plans_ref = st.session_state.db.collection("users").document(user_id).collection("meal_plans").order_by("timestamp", direction=firestore.Query.DESCENDING).limit(10)
            plans = plans_ref.stream()
            print(f"Found plans for {user_id}: {[doc.id for doc in plans]}")
            history = []
            for doc in plans:
                data = doc.to_dict()
                timestamp = data.get("timestamp", "No time")
                history.append({
                    "Timestamp": timestamp,
                    "Protein (g)": data.get("protein_g", ""),
                    "Carbs (g)": data.get("carbs_g", ""),
                    "Fat (g)": data.get("fat_g", ""),
                    "Diet": data.get("diet_type", ""),
                    "Meal Plan": data.get("meal_plan", "")
                })
            if history:
                df = pd.DataFrame(history)
                st.dataframe(df)
            else:
                st.info("No meal plans found for this user.")
        except Exception as e:
            st.error(f"Failed to load user history: {e}")

        # ✅ WHOOP Token Refresh
        refresh_result = refresh_whoop_token(user_id)
        if "error" in refresh_result:
            st.warning("⚠️ WHOOP token could not be refreshed.")
        else:
            st.success("🔄 WHOOP token refreshed successfully.")

            # ✅ WHOOP Metric Fetch
            def fetch_whoop_data(user_id):
                token_doc = st.session_state.db.collection("users").document(user_id).collection("whoop_auth").document("token").get()
                if not token_doc.exists:
                    return None, None, "No WHOOP token found."

                token_data = token_doc.to_dict()
                access_token = token_data.get("access_token")
                if not access_token:
                    return None, None, "Access token missing."

                headers = {"Authorization": f"Bearer {access_token}"}
                try:
                    recovery_resp = requests.get("https://api.prod.whoop.com/v1/recovery", headers=headers)
                    strain_resp = requests.get("https://api.prod.whoop.com/v1/strain", headers=headers)

                    if recovery_resp.status_code == 200 and strain_resp.status_code == 200:
                        return recovery_resp.json(), strain_resp.json(), None
                    else:
                        return None, None, f"API Error: {recovery_resp.status_code}, {strain_resp.status_code}"
                except Exception as e:
                    return None, None, str(e)

            # ✅ WHOOP Display
            st.subheader("📈 WHOOP Metrics")

            recovery_data, strain_data, whoop_error = fetch_whoop_data(user_id)

            if whoop_error:
                st.error(f"Failed to fetch WHOOP data: {whoop_error}")
            else:
                if recovery_data and "records" in recovery_data and recovery_data["records"]:
                    latest_recovery = recovery_data["records"][0]
                    st.metric("Recovery Score", latest_recovery.get("score", "N/A"))
                    st.write(f"🛌 Sleep Quality: {latest_recovery.get('sleep', {}).get('quality_duration', 'N/A')} mins")
                    st.write(f"💓 HRV: {latest_recovery.get('hrv', 'N/A')} ms")
                else:
                    st.info("No recovery data available.")

                if strain_data and "records" in strain_data and strain_data["records"]:
                    latest_strain = strain_data["records"][0]
                    st.metric("Strain Score", latest_strain.get("score", "N/A"))
                    st.write(f"📅 Date: {latest_strain.get('created_at', 'N/A')}")
                else:
                    st.info("No strain data available.")
