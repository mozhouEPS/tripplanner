import streamlit as st
import requests
import googlemaps
from openai import OpenAI
import pandas as pd

# ----------------------------
# 1. Configuration
# ----------------------------

# Load API keys from Streamlit secrets
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
WEATHER_API_KEY = st.secrets["WEATHER_API_KEY"]
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
            daily_forecast.append(f"{weather}, avg temp {temp}°C")
    return daily_forecast

def get_poi(city, interests, max_results=5):
    poi_list = []
    type_mapping = {
        "museums": "museum",
        "parks": "park",
        "food": "restaurant",
        "landmark": "tourist_attraction"
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
    For each day, include the weather forecast: {', '.join(weather_forecast)}.
    Points of interest: {', '.join(poi_list)}.
    For each day, suggest activities and explain why each choice is good based on the weather.
    Include timing suggestions and avoid too many activities in one day.
    """
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=700
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
    ["museums", "parks", "food", "landmark"],
    default=["museums", "food"]
)

if st.button("Generate Itinerary"):
    with st.spinner("Fetching weather..."):
        weather_forecast = get_weather(city, days)

    with st.spinner("Fetching points of interest..."):
        poi_list = get_poi(city, interests)

    with st.spinner("Generating itinerary with AI..."):
        itinerary = generate_itinerary(city, days, interests, weather_forecast, poi_list)

    # Show weather table
    st.subheader("🌤 Daily Weather Forecast")
    df = pd.DataFrame({
        "Day": [f"Day {i+1}" for i in range(days)],
        "Weather": weather_forecast
    })
    st.table(df)

    # Show itinerary
    st.subheader("📅 Your Trip Itinerary")
    st.write(itinerary)
