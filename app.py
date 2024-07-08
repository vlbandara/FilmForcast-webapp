
import streamlit as st
import google.generativeai as genai
from google.generativeai.types import SafetySettingDict, HarmCategory, HarmBlockThreshold
import aiohttp
import asyncio
import json
import re
from typing import List, Dict, Any
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configure the Gemini API key
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=GEMINI_API_KEY)

# OMDB API key
OMDB_API_KEY = st.secrets["OMDB_API_KEY"]

# Set up the Gemini model with adjusted safety settings
safety_settings = [
    SafetySettingDict(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
    SafetySettingDict(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
    SafetySettingDict(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
    SafetySettingDict(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
]

model = genai.GenerativeModel('gemini-1.5-pro', safety_settings=safety_settings)

# Streamlit app
st.set_page_config(page_title="FilmForcast", page_icon="🎬", layout="wide")
st.title("FilmForcast Based on Your Day 🎬")

# Initialize session state
if "movies" not in st.session_state:
    st.session_state.movies = []
if "favorites" not in st.session_state:
    st.session_state.favorites = []
if "watch_history" not in st.session_state:
    st.session_state.watch_history = []

async def get_movie_details(session: aiohttp.ClientSession, title: str, year: str) -> Dict[str, Any]:
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}&y={year}"
    async with session.get(url) as response:
        if response.status == 200:
            data = await response.json()
            if data.get("Response") == "True":
                return data
    return None

def analyze_day(day_description: str) -> Dict[str, List[str]]:
    prompt = f"""
    Analyze the following description of someone's day and identify:
    1. The overall mood (e.g., happy, stressed, relaxed)
    2. Key activities or events mentioned
    3. Any specific interests or preferences implied
    4. The likely energy level of the person (high, medium, low)
    5. Any emotional needs that might be addressed by watching a movie

    Day description: "{day_description}"

    Provide your analysis in the following JSON format:
    {{
        "mood": ["mood1", "mood2"],
        "activities": ["activity1", "activity2"],
        "interests": ["interest1", "interest2"],
        "energy_level": "energy level",
        "emotional_needs": ["need1", "need2"]
    }}
    """
    
    try:
        response = model.generate_content(prompt)
        analysis = json.loads(response.text)
        return analysis
    except json.JSONDecodeError:
        st.error("Error parsing the response from Gemini. The response was not in valid JSON format.")
        return None
    except Exception as e:
        st.error(f"Error in analyzing day: {str(e)}")
        return None

def display_day_analysis(analysis: Dict[str, List[str]]):
    st.subheader("Understanding Your Day")

    cols = st.columns(3)
    with cols[0]:
        st.write("**Mood:**")
        for mood in analysis.get("mood", []):
            st.write(f"- {mood.strip()}")
        
        st.write("**Energy level:**")
        st.write(f"- {analysis.get('energy_level', 'Not specified')}")

    with cols[1]:
        st.write("**Emotional Needs:**")
        for need in analysis.get("emotional_needs", []):
            st.write(f"- {need.strip()}")
        
        st.write("**Activities:**")
        for activity in analysis.get("activities", []):
            st.write(f"- {activity.strip()}")

    with cols[2]:
        st.write("**Interests:**")
        for interest in analysis.get("interests", []):
            st.write(f"- {interest.strip()}")
    
    if not any(analysis.values()):
        st.warning("No specific details could be extracted from the analysis.")

def parse_recommendations(text: str) -> List[Dict[str, str]]:
    movies = []
    pattern = r"\d+\.\s+\*\*Title:\*\*\s+(.*?)\s+\*\*Year:\*\*\s+(\d{4})\s+\*\*Reason:\*\*\s+(.*?)(?=\n\d+\.|\Z)"
    matches = re.findall(pattern, text, re.DOTALL)
    for match in matches:
        movies.append({
            "title": match[0].strip('*'),
            "year": match[1],
            "reason": match[2].strip()
        })
    return movies

def get_movie_recommendations(analysis: Dict[str, List[str]]) -> List[Dict[str, str]]:
    prompt = f"""
    Based on the following analysis of someone's day, recommend 5 movies that would be suitable for them to watch. 
    Consider their mood, activities, interests, energy level, and emotional needs when making your recommendations.
    Also, take into account their watch history to avoid recommending movies they've already seen.

    Analysis:
    {json.dumps(analysis, indent=2)}

    Watch History:
    {', '.join([f"{movie['title']} ({movie['year']})" for movie in st.session_state.watch_history])}

    For each movie, provide:
    1. Title
    2. Year of release
    3. A detailed explanation of why this movie is recommended based on the person's day (at least 3 sentences)

    Format your response exactly as follows:
    1. **Title:** [Movie Title]
       **Year:** [Year]
       **Reason:** [Detailed explanation]

    2. **Title:** [Movie Title]
       **Year:** [Year]
       **Reason:** [Detailed explanation]

    And so on for all 5 recommendations.
    """
    
    try:
        response = model.generate_content(prompt)
        recommendations = parse_recommendations(response.text)
        if not recommendations:
            st.error("No recommendations found in the response. API Response:")
            st.text(response.text)
            return None
        return recommendations
    except Exception as e:
        st.error(f"Error in getting recommendations: {str(e)}")
        st.text("API Response:")
        st.text(response.text)
        return None

# User input
day_description = st.text_area("How was your day? Describe it in detail:", height=150)

if st.button("Get Personalized Movie Recommendations"):
    if day_description:
        with st.spinner("Analyzing your day and generating recommendations..."):
            analysis = analyze_day(day_description)
            if analysis:
                display_day_analysis(analysis)
                
                recommendations = get_movie_recommendations(analysis)
                if recommendations:
                    st.session_state.movies = recommendations
                else:
                    st.error("Unable to generate recommendations. Please try again.")
            else:
                st.error("Unable to analyze your day. Please try again with a more detailed description.")
    else:
        st.warning("Please describe your day before requesting recommendations.")

# Display recommendations
if st.session_state.movies:
    st.subheader("Your Personalized Movie Recommendations:")
    
    async def fetch_movie_details():
        async with aiohttp.ClientSession() as session:
            tasks = [get_movie_details(session, movie['title'], movie['year']) for movie in st.session_state.movies]
            return await asyncio.gather(*tasks)

    movie_details = asyncio.run(fetch_movie_details())

    for index, (movie, details) in enumerate(zip(st.session_state.movies, movie_details)):
        with st.container():
            st.markdown(f"### Recommendation {index + 1}")
            cols = st.columns([1, 2])
            with cols[0]:
                st.markdown(f"**{movie['title']} ({movie['year']})**")
                if details and details.get("Poster") != "N/A":
                    st.image(details["Poster"], width=200)
                else:
                    st.write("No image available.")
            with cols[1]:
                st.write(f"**Why we recommend this movie:** {movie['reason']}")
                if details:
                    st.write(f"**Director:** {details.get('Director', 'N/A')}")
                    st.write(f"**Cast:** {details.get('Actors', 'N/A')}")
                    st.write(f"**Genre:** {details.get('Genre', 'N/A')}")
                    st.write(f"**IMDb Rating:** {details.get('imdbRating', 'N/A')}")
                    with st.expander("Plot"):
                        st.write(details.get('Plot', 'N/A'))
                else:
                    st.write("Detailed information not available.")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Add to Favorites", key=f"fav_{index}"):
                        if movie not in st.session_state.favorites:
                            st.session_state.favorites.append(movie)
                            st.success(f"{movie['title']} added to favorites!")
                        else:
                            st.info(f"{movie['title']} is already in your favorites.")
                
                with col2:
                    if st.button(f"Mark as Watched", key=f"watch_{index}"):
                        if movie not in st.session_state.watch_history:
                            movie_with_date = movie.copy()
                            movie_with_date['watch_date'] = datetime.now().strftime("%Y-%m-%d")
                            movie_with_date['genre'] = details.get('Genre', 'Unknown') if details else 'Unknown'
                            st.session_state.watch_history.append(movie_with_date)
                            st.success(f"{movie['title']} added to watch history!")
                        else:
                            st.info(f"{movie['title']} is already in your watch history.")
            
            st.markdown("---")  # Add a horizontal line between movies
else:
    st.info("No movie recommendations to display. Please describe your day to get personalized recommendations.")

# Sidebar for API key input and additional features
with st.sidebar:
    st.subheader("Configuration")
    gemini_api_key = st.text_input("Enter your Gemini API Key:", type="password", value=GEMINI_API_KEY)
    omdb_api_key = st.text_input("Enter your OMDB API Key:", type="password", value=OMDB_API_KEY)
    if gemini_api_key and omdb_api_key:
        genai.configure(api_key=gemini_api_key)
        OMDB_API_KEY = omdb_api_key
        st.success("API Keys configured successfully!")

    if st.button("Clear Recommendations"):
        st.session_state.movies = []
        st.experimental_rerun()

    # Favorites Section
    st.subheader("My Favorite Movies")
    if st.session_state.favorites:
        for fav in st.session_state.favorites:
            st.write(f"- {fav['title']} ({fav['year']})")
    else:
        st.write("No favorites added yet.")

    # Watch History Section
    st.subheader("My Watch History")
    if st.session_state.watch_history:
        for watched in st.session_state.watch_history:
            st.write(f"- {watched['title']} ({watched['year']}) - Watched on {watched['watch_date']}")
    else:
        st.write("No watch history yet.")
# New feature: Movie Insights
st.subheader("Movie Insights")
if st.session_state.watch_history:
    # Prepare data for visualization
    df = pd.DataFrame(st.session_state.watch_history)
    df['watch_date'] = pd.to_datetime(df['watch_date'])
    
    try:
        # Genre distribution
        if 'genre' in df.columns:
            genre_counts = df['genre'].str.split(', ', expand=True).stack().value_counts()
            fig_genre = px.pie(values=genre_counts.values, names=genre_counts.index, title="Genre Distribution")
            st.plotly_chart(fig_genre)
        else:
            st.write("Genre information is not available for insights.")
    except Exception as e:
        st.error(f"An error occurred while creating the genre distribution plot: {str(e)}")

    st.write("Wait for updated to get more insights!")

else:
    st.write("Start watching movies to see insights!")

# Footer
st.markdown("---")
st.markdown("Created with ❤️ by Vinodh Lahiru")
