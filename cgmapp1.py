# ✅ Fully Merged NutriAI + CGM-WHOOP App with OAuth Redirect Integration
# -------------------------------------------------------

import streamlit as st
import requests
import json
import os
import openai
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from io import StringIO
from fastapi import FastAPI
from auth_fastapi_module import router
import plotly.graph_objects as go
from urllib.parse import urlparse, parse_qs
# Set up OpenAI API key from secrets
openai.api_key = st.secrets["OPENAI_API_KEY"]
client = openai

# WHOOP credentials from Streamlit secrets

import streamlit as st

# Move secret loading into a function or use try-except at module level
try:
    # Attempt to load secrets
    WHOOP_CLIENT_ID = st.secrets["WHOOP_CLIENT_ID"]
    WHOOP_CLIENT_SECRET = st.secrets["WHOOP_CLIENT_SECRET"]
    WHOOP_REDIRECT_URI = "https://cgmapp1py-cke3lbga3zvnszbci6gegb.streamlit.app/"
except KeyError as e:
    # Show error in the app
    st.error(f"❌ Missing secret: {e}")
    st.error("Please add WHOOP_CLIENT_ID and WHOOP_CLIENT_SECRET to your Streamlit secrets.")
    
    # Show available secrets (be careful with this in production!)
    st.write("Available secrets:", list(st.secrets.keys()) if hasattr(st, 'secrets') else "No secrets found")
    
    # Set None values to prevent further errors
    WHOOP_CLIENT_ID = None
    WHOOP_CLIENT_SECRET = None
    WHOOP_REDIRECT_URI = None
    
    # Stop the app execution
    st.stop()


# WHOOP endpoints
TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
AUTH_URL = (
    f"https://api.prod.whoop.com/oauth/oauth2/auth?client_id={WHOOP_CLIENT_ID}"
    f"&redirect_uri={WHOOP_REDIRECT_URI}&response_type=code&scope=read:recovery read:sleep read:strain"
)
RECOVERY_URL = "https://api.prod.whoop.com/recovery/v1"
SLEEP_URL = "https://api.prod.whoop.com/sleep/v1"
STRAIN_URL = "https://api.prod.whoop.com/strain/v1"

# Sidebar Navigation
page = st.sidebar.radio("Navigate", [
    "Nutrition Profile",
    "ChatGPT Meal Plan",
    "USDA Food Search",
    "Glucose & Chat",
    "WHOOP + CGM Adjustments",
    "Insulin Resistance",
    "Glucose Trend Charts",
    "Metabolic Adaptation Score"
])

# WHOOP Login Button
st.sidebar.subheader("Connect WHOOP")
if "whoop_access_token" not in st.session_state:
    st.sidebar.markdown(f"[🔗 Connect to WHOOP]({AUTH_URL})")

# Parse WHOOP code from URL
query_params = st.query_params
if "code" in query_params and "whoop_access_token" not in st.session_state:
    whoop_code = query_params["code"]
    token_payload = {
        "grant_type": "authorization_code",
        "code": whoop_code,
        "client_id": WHOOP_CLIENT_ID,
        "client_secret": WHOOP_CLIENT_SECRET,
        "redirect_uri": WHOOP_REDIRECT_URI
    }
    token_response = requests.post(TOKEN_URL, data=token_payload)
    if token_response.status_code == 200:
        access_token = token_response.json().get("access_token")
        st.session_state["whoop_access_token"] = access_token
        st.success("✅ WHOOP connected successfully!")
    else:
        st.error("❌ Failed to authenticate with WHOOP.")

# Automatically fetch and inject WHOOP data
whoop_data = {"strain": 12, "recovery": 65, "sleep": 7.5}  # defaults
if "whoop_access_token" in st.session_state:
    headers = {"Authorization": f"Bearer {st.session_state['whoop_access_token']}"}
    start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        r = requests.get(f"{RECOVERY_URL}?start={start_date}&end={end_date}", headers=headers).json()
        s = requests.get(f"{SLEEP_URL}?start={start_date}&end={end_date}", headers=headers).json()
        t = requests.get(f"{STRAIN_URL}?start={start_date}&end={end_date}", headers=headers).json()

        whoop_data["recovery"] = r["records"][0]["score"] if r["records"] else 65
        whoop_data["sleep"] = round(s["records"][0]["hours"] if s["records"] else 7.5, 1)
        whoop_data["strain"] = round(t["records"][0]["score"] if t["records"] else 12, 1)
    except:
        st.warning("⚠️ Using default WHOOP values due to fetch error.")


# Automatically fetch and inject WHOOP data
whoop_data = {"strain": 12, "recovery": 65, "sleep": 7.5}  # defaults
if "whoop_access_token" in st.session_state:
    headers = {"Authorization": f"Bearer {st.session_state['whoop_access_token']}"}
    start_date = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")

    try:
        r = requests.get(f"{RECOVERY_URL}?start={start_date}&end={end_date}", headers=headers).json()
        s = requests.get(f"{SLEEP_URL}?start={start_date}&end={end_date}", headers=headers).json()
        t = requests.get(f"{STRAIN_URL}?start={start_date}&end={end_date}", headers=headers).json()

        whoop_data["recovery"] = r["records"][0]["score"] if r["records"] else 65
        whoop_data["sleep"] = round(s["records"][0]["hours"] if s["records"] else 7.5, 1)
        whoop_data["strain"] = round(t["records"][0]["score"] if t["records"] else 12, 1)
    except:
        st.warning("⚠️ Using default WHOOP values due to fetch error.")

# Inject WHOOP values into adaptive engine
if page == "WHOOP + CGM Adjustments":
    st.title("💪 WHOOP + CGM Adaptive Nutrition Engine")

    strain = whoop_data["strain"]
    recovery = whoop_data["recovery"]
    sleep_hours = whoop_data["sleep"]
    st.write(f"WHOOP Data Used — Strain: {strain}, Recovery: {recovery}, Sleep: {sleep_hours}h")

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


# ✅ FastAPI (not used by Streamlit unless run externally)
app = FastAPI()
app.include_router(router)

@app.get("/")
def read_root():
    return {
        "status": "✅ FastAPI is running",
        "message": "Welcome to your CGM + WHOOP + GPT API"
    }





        
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
        except Exception as e:
            st.error(f"Error generating meal plan with ChatGPT: {str(e)}")

# ========== PAGE 3: Glucose & Chat ==========
elif page == "Glucose & Chat":
    st.title("📊 NutriAI: Daily Glucose & Macro Planner")

    with st.form("glucose_form"):
        user_id = st.text_input("Enter your name or user ID:", "david")
        st.session_state.user_id = user_id
        bodyweight = st.number_input("Bodyweight (kg)", min_value=30.0, max_value=150.0, value=75.0)
        goal = st.selectbox("Goal", ["cut", "maintain", "gain"])
        glucose_data = st.text_area("Format: HH:MM,glucose (one per line)", "08:00,95 09:00,142 10:00,135")
        submitted = st.form_submit_button("Analyze")

    if submitted:
        try:
            lines = glucose_data.strip().split(" ")
            readings = [{"time": t.strip(), "glucose": int(v.strip())} for t, v in (line.split(",") for line in lines)]
            payload = {
                "glucose_readings": readings,
                "bodyweight_kg": bodyweight,
                "goal": goal
            }
            response = requests.post("http://localhost:8000/analyze", json=payload)
            if response.status_code == 200:
                st.session_state.response = response.json()
                st.success("✅ Analysis complete!")
                st.metric("Time in Range (%)", st.session_state.response["tir"])
                st.metric("# Spikes", len(st.session_state.response["spikes"]))
                st.metric("# Lows", len(st.session_state.response["lows"]))
                st.subheader("🥩 Daily Macros")
                st.json(st.session_state.response["macros"])
                st.subheader("🧠 Recommendation")
                st.write(st.session_state.response["recommendation"])
            else:
                st.error(f"API Error: {response.status_code}")
        except Exception as e:
            st.error(f"Error: {str(e)}")

    if st.session_state.response:
        st.subheader("💬 Ask NutriAI Anything")
        user_input = st.text_input("Ask a question about your results:", "")

        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            tir = st.session_state.response["tir"]
            spikes = st.session_state.response["spikes"]
            lows = st.session_state.response["lows"]
            macros = st.session_state.response["macros"]

            if "spike" in user_input.lower():
                if spikes:
                    s = spikes[-1]
                    reply = f"You had a glucose spike from {s['from']} to {s['to']} with a +{s['delta']} mg/dL increase."
                else:
                    reply = "No spikes were recorded today."
            elif "low" in user_input.lower():
                if lows:
                    l = lows[-1]
                    reply = f"You had a low at {l['time']} with {l['value']} mg/dL. Try a protein+fat snack."
                else:
                    reply = "No glucose lows today."
            elif "macro" in user_input.lower():
                reply = f"Today's macros are: Protein {macros['protein_g']}g, Carbs {macros['carbs_g']}g, Fat {macros['fat_g']}g."
            elif "recommendation" in user_input.lower():
                reply = st.session_state.response["recommendation"]
            else:
                reply = "Ask about spikes, lows, macros, or recommendation."

            st.session_state.messages.append({"role": "assistant", "content": reply})
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"chat_logs/{user_id}_{timestamp}.json"
            st.session_state.chat_file = filename
            with open(filename, "w") as f:
                json.dump(st.session_state.messages, f, indent=2)

        for msg in st.session_state.messages:
            st.markdown(f"**{'You' if msg['role'] == 'user' else 'NutriAI'}:** {msg['content']}")

        if st.session_state.chat_file:
            with open(st.session_state.chat_file, "r") as f:
                chat_json = f.read()
            st.download_button("📥 Download Chat History", chat_json, file_name=os.path.basename(st.session_state.chat_file), mime="application/json")



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


#===============USDA Food Search Function========================
if page == "USDA Food Search":
    st.title("🔍 Search Real Foods From USDA Database")
    with st.form("usda_form"):
        search_term = st.text_input("Type a food to look up:", value="chicken breast")
        usda_search = st.form_submit_button("Search USDA Foods")

    if 'usda_search' in locals() and usda_search:
        # Placeholder USDA search function until implemented
        results = search_usda_foods(search_term)
        if results:
            st.success(f"Top {len(results)} results for '{search_term}':")
            for food in results:
                st.write(f"**{food['description']}**")
                nutrients = food.get("foodNutrients", [])
                macros = {"Protein": None, "Carbohydrate, by difference": None, "Total lipid (fat)": None, "Energy": None}
                for nutrient in nutrients:
                    name = nutrient['nutrientName']
                    if name in macros:
                        macros[name] = f"{nutrient['value']} {nutrient['unitName']}"
                st.write(f"- Calories: {macros['Energy']}")
                st.write(f"- Protein: {macros['Protein']}")
                st.write(f"- Carbs: {macros['Carbohydrate, by difference']}")
                st.write(f"- Fat: {macros['Total lipid (fat)']}")

                # Auto-match feedback
                st.caption("📊 Matching this item to your current macros...")
                if 'protein_g' in st.session_state and 'carbs_g' in st.session_state and 'fat_g' in st.session_state:
                    def extract_numeric(val):
                        try:
                            return float(str(val).split()[0])
                        except:
                            return 0.0

                    p_goal = st.session_state.protein_g
                    c_goal = st.session_state.carbs_g
                    f_goal = st.session_state.fat_g

                    p_val = extract_numeric(macros['Protein'])
                    c_val = extract_numeric(macros['Carbohydrate, by difference'])
                    f_val = extract_numeric(macros['Total lipid (fat)'])

                    match_score = 100 - (
                        abs(p_val - (p_goal / 4)) / (p_goal / 4) * 33 +
                        abs(c_val - (c_goal / 4)) / (c_goal / 4) * 33 +
                        abs(f_val - (f_goal / 4)) / (f_goal / 4) * 33
                    )
                    match_score = max(0, min(100, round(match_score)))
                    st.write(f"🧮 Match Score: {match_score}% to your current macro target (1 of 4 meals)")
                save_key = f"save_{food['fdcId']}"
                if st.button("💾 Save this to my daily plan", key=save_key):
                    saved_meal = {
                        "description": food['description'],
                        "calories": macros['Energy'],
                        "protein": macros['Protein'],
                        "carbs": macros['Carbohydrate, by difference'],
                        "fat": macros['Total lipid (fat)']
                    }
                    if "saved_meals" not in st.session_state:
                        st.session_state.saved_meals = []
                    st.session_state.saved_meals.append(saved_meal)
                    st.success(f"✔️ Added {food['description']} to your daily plan.")
                st.markdown("---")
        else:
            st.warning("No results found.")
        


