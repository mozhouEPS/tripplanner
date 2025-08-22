import streamlit as st
import requests
import googlemaps
from openai import OpenAI

# ----------------------------
# 1. Configuration
# ----------------------------

# Load keys
# with open("openai.txt", "r") as f:
#     OPENAI_API_KEY = f.read().strip()

# WEATHER_API_KEY = "aa4f8ce605d4aae238fd7c9cd8025ed6"
# GMAPS_API_KEY = "AIzaSyANAzQPNhqiksExsM4RYxT4Zvr7Ld24_uw"

import streamlit as st
import os

# Example: OpenAI
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

# Example: Weather API
WEATHER_API_KEY = st.secrets["WEATHER_API_KEY"]

# Example: Google Maps
GMAPS_API_KEY = st.secrets["GOOGLE_MAPS_API_KEY"]


# Clients
client = OpenAI(api_key=OPENAI_API_KEY)
gmaps = googlemaps.Client(key=GMAPS_API_KEY)


# ----------------------------
# 2. Helper functions
# ----------------------------

def get_weather(city, days):
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&units=metric&appid={WEATHER_API_KEY}"
    response = requests.get(url)
    data = response.json()

    if "list" not in data:
        return ["Weather unavailable"] * days

    daily_forecast = []
    for i in range(days):
        if i*8 < len(data['list']):
            weather = data['list'][i*8]['weather'][0]['description']
            temp = data['list'][i*8]['main']['temp']
            daily_forecast.append(f"Day {i+1}: {weather}, avg temp {temp}°C")
    return daily_forecast


def get_poi(city, interests, max_results=5):
    poi_list = []
    type_mapping = {
        "museums": "museum",
        "parks": "park",
        "food": "restaurant"
    }
    for interest in interests:
        place_type = type_mapping.get(interest, "")
        results = gmaps.places(query=f"{interest} in {city}", type=place_type)
        for place in results.get('results', [])[:max_results]:
            poi_list.append(place['name'])
    return poi_list


def generate_itinerary(city, days, interests, weather_forecast, poi_list):
    prompt = f"""
    You are a travel assistant. Generate a {days}-day trip itinerary for {city}.
    User interests: {', '.join(interests)}.
    Weather forecast: {', '.join(weather_forecast)}.
    Points of interest: {', '.join(poi_list)}.
    Distribute activities each day, include timing suggestions, and avoid too many activities in one day.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=600
    )
    return response.choices[0].message.content.strip()


# ----------------------------
# 3. Streamlit UI
# ----------------------------

st.title("🌍 AI Trip Planner")

st.write("Plan your trip with weather, points of interest, and AI-generated itineraries.")

# Inputs
city = st.text_input("Destination city", "Paris")
days = st.number_input("Number of days", min_value=1, max_value=14, value=3)

interests = st.multiselect(
    "Select your interests",
    ["museums", "parks", "food"],
    default=["museums", "food"]
)

if st.button("Generate Itinerary"):
    with st.spinner("Fetching weather..."):
        weather_forecast = get_weather(city, days)

    with st.spinner("Fetching points of interest..."):
        poi_list = get_poi(city, interests)

    with st.spinner("Generating itinerary with AI..."):
        itinerary = generate_itinerary(city, days, interests, weather_forecast, poi_list)

    st.subheader("📅 Your Trip Itinerary")
    st.write(itinerary)
