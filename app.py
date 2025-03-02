import streamlit as st
import requests
import time
import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.output_parsers import StrOutputParser

st.set_page_config(page_title="AI Trip Planner", layout="centered", page_icon="🌍")

st.markdown(
    """
      <div class="banner-container">
        <img src="https://t4.ftcdn.net/jpg/00/65/48/25/360_F_65482539_C0ZozE5gUjCafz7Xq98WB4dW6LAhqKfs.jpg" class="banner-img">
    </div>
    
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Raleway:wght@400;600&display=swap');

        * {
            font-family: 'Raleway', sans-serif !important;
        }
        .banner-container { text-align: center; margin-bottom: 20px; }
        .banner-img { width: 100%; max-height: 250px; object-fit: cover; border-radius: 15px; }
        body {
            background-size: cover;
            color: black;
           font-family: 'Montserrat', sans-serif !important;

        }
        .main {
            background: rgba(255, 255, 255, 0.8);
            padding: 20px;
            border-radius: 15px;
            backdrop-filter: blur(10px);
            color: black;
        }
        h1 {
            text-align: center;
            color: black;
        }
        p {
            text-align: center;
            color: black;
        }
        
    </style>
  
    """,
    unsafe_allow_html=True
)

st.title("📺 Smart Travel Guide ✈️")
st.write("Enter your travel details to receive estimated costs for multiple transport modes and check if the weather is suitable for travel.")

start_location = st.text_input("📍 Departure Location:", placeholder="Enter your starting point")
end_location = st.text_input("📍 Destination:", placeholder="Enter your destination")
weather_preference = st.selectbox("🌤️ Preferred Weather:", ["Hot", "Cold", "Moderate"])

def fetch_weather(city):
    api_key = "your_openweather_api_key"
    weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    
    try:
        response = requests.get(weather_url)
        data = response.json()
        if response.status_code == 200 and "main" in data:
            temperature = data["main"]["temp"]
            conditions = data["weather"][0]["description"]
            return temperature, conditions
        else:
            return None, "Invalid city or data unavailable"
    except Exception as e:
        return None, f"Error: {e}"

def parse_travel_response(response):
    rows = []
    for line in response.split("\n"):
        parts = [p.replace("*", "").strip() for p in line.split(" | ")]
        if len(parts) == 4:
            rows.append(parts)
    return pd.DataFrame(rows, columns=["Mode of Transport", "Estimated Fare", "Duration", "Additional Info"]) if rows else None

if st.button("Generate Travel Plan"):
    if start_location and end_location:
        with st.spinner("🔍 Searching for the best travel options..."):
            time.sleep(2)
            travel_prompt = ChatPromptTemplate.from_template(
                """
                You are an AI travel consultant helping users find the best travel plans.
                Provide a detailed theoretical explanation of travel options from {start_location} to {end_location} first.
                After the theory, give structured travel options in the format:
                Mode of Transport | Estimated Fare | Duration | Additional Info
                """
            )
            travel_assistant = ChatGoogleGenerativeAI(api_key="your_gemini_api_key", model="gemini-2.0-flash-exp")
            output_parser = StrOutputParser()
            travel_chain = travel_prompt | travel_assistant | output_parser
            travel_response = travel_chain.invoke({"start_location": start_location, "end_location": end_location})

            theory_part, _, table_part = travel_response.partition("Mode of Transport | Estimated Fare | Duration | Additional Info")
            st.markdown("### 📝 Travel Plan Explanation")
            st.write(theory_part.strip())
            travel_df = parse_travel_response(table_part)
            if travel_df is not None:
                st.markdown("### 📊 Travel Options Table")
                st.dataframe(travel_df)
           

        temperature, conditions = fetch_weather(end_location)
        if temperature is not None:
            st.write(f"🌡️ Temperature in {end_location}: **{temperature}°C**")
            st.write(f"🌦️ Weather Condition: **{conditions.capitalize()}**")
            match_message = "✅ The weather matches your preference!" if (
                (weather_preference == "Cold" and temperature < 15) or
                (weather_preference == "Hot" and temperature > 30) or
                (weather_preference == "Moderate" and 15 <= temperature <= 30)) else "⚠️ The weather does not match your preference."
            st.info(match_message)
        else:
            st.error(f"⚠️ Unable to fetch weather: {conditions}")
    else:
        st.error("❌ Please enter both departure and destination locations.")
