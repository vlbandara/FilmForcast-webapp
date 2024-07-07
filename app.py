
import streamlit as st
import google.generativeai as genai
from google.generativeai.types import SafetySettingDict, HarmCategory, HarmBlockThreshold
import requests
import json
import re

# Configure the Gemini API key
GEMINI_API_KEY = "AIzaSyByhzdtQI7yhUNLGjuV6CtBv3nCfDNnePw"
genai.configure(api_key=GEMINI_API_KEY)

# OMDB API key
OMDB_API_KEY = "ba6d1912"

# Set up the Gemini model with adjusted safety settings
safety_settings = [
    SafetySettingDict(category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
    SafetySettingDict(category=HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
    SafetySettingDict(category=HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
    SafetySettingDict(category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=HarmBlockThreshold.BLOCK_ONLY_HIGH),
]

model = genai.GenerativeModel('gemini-1.5-pro', safety_settings=safety_settings)

# Streamlit app
st.title("Robust Movie Recommender Based on Your Day 🎬")

# Initialize session state
if "movies" not in st.session_state:
    st.session_state.movies = []

def get_movie_details(title, year):
    url = f"http://www.omdbapi.com/?apikey={OMDB_API_KEY}&t={title}&y={year}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("Response") == "True":
            return data
    return None

def analyze_day(day_description):
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
        "energy_level": ["energy level"],
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
    

def parse_day_analysis(raw_text):
    analysis = {
        "mood": [],
        "activities": [],
        "interests": [],
        "energy_level": [],  
        "emotional_needs": []
    }

    # Extract energy
    energy_match = re.search(r'energy:?\s*(.*?)(?:\n|$)', raw_text, re.IGNORECASE | re.DOTALL)
    if energy_match:
        energy = re.findall(r'\[([^\]]+)\]', energy_match.group(1))
        analysis["energy_level"] = [item.strip() for sublist in energy for item in sublist.split(',')]  # Changed from "energy" to "energy_level"

    # ... rest of the function remains the same
    # Extract mood
    mood_match = re.search(r'mood:?\s*(.*?)(?:\n|$)', raw_text, re.IGNORECASE | re.DOTALL)
    if mood_match:
        mood = re.findall(r'\[([^\]]+)\]', mood_match.group(1))
        analysis["mood"] = [item.strip() for sublist in mood for item in sublist.split(',')]

    # Extract activities
    activities_match = re.search(r'activities:?\s*(.*?)(?:\n|$)', raw_text, re.IGNORECASE | re.DOTALL)
    if activities_match:
        activities = re.findall(r'\[([^\]]+)\]', activities_match.group(1))
        analysis["activities"] = [item.strip() for sublist in activities for item in sublist.split(',')]

    # Extract interests
    interests_match = re.search(r'interests:?\s*(.*?)(?:\n|$)', raw_text, re.IGNORECASE | re.DOTALL)
    if interests_match:
        interests = re.findall(r'\[([^\]]+)\]', interests_match.group(1))
        analysis["interests"] = [item.strip() for sublist in interests for item in sublist.split(',')]

    # Extract emotional needs
    needs_match = re.search(r'emotional needs:?\s*(.*?)(?:\n|$)', raw_text, re.IGNORECASE | re.DOTALL)
    if needs_match:
        needs = re.findall(r'\[([^\]]+)\]', needs_match.group(1))
        analysis["emotional_needs"] = [item.strip() for sublist in needs for item in sublist.split(',')]

    return analysis

def display_day_analysis(analysis):
    st.subheader("Understanding Your Day")

    if analysis.get("mood"):
        st.write("**Mood:**")
        for mood in analysis["mood"]:
            st.write(f"- {mood.strip()}")

    if analysis.get("energy_level"):
        st.write("**Energy level:**")
        for energy in analysis["energy_level"]:
            st.write(f"- {energy.strip()}")

    if analysis.get("emotional_needs"):
        st.write("**Emotional Needs:**")
        for need in analysis["emotional_needs"]:
            st.write(f"- {need.strip()}")
    else:
        st.write("**Emotional Needs:** Not enough information provided.")
    
    if analysis.get("activities"):
        st.write("**Activities:**")
        for activity in analysis["activities"]:
            st.write(f"- {activity.strip()}")
    else:
        st.write("**Activities:** Not enough information provided.")
    
    if analysis.get("interests"):
        st.write("**Interests:**")
        for interest in analysis["interests"]:
            st.write(f"- {interest.strip()}")
    else:
        st.write("**Interests:** Not enough information provided.")
    
    if not any(analysis.values()):
        st.warning("No specific details could be extracted from the analysis.")

def parse_recommendations(text):
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

def get_movie_recommendations(analysis):
    prompt = f"""
    Based on the following analysis of someone's day, recommend 5 movies that would be suitable for them to watch. 
    Consider their mood, activities, interests, energy level, and emotional needs when making your recommendations.

    Analysis:
    {json.dumps(analysis, indent=2) if isinstance(analysis, dict) else analysis}

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
    for movie in st.session_state.movies:
        details = get_movie_details(movie['title'], movie['year'])
        with st.container():
            st.markdown(f"### {movie['title']} ({movie['year']})")
            if details and details.get("Poster") != "N/A":
                st.image(details["Poster"], width=200)
            else:
                st.write("No image available.")
            st.write(f"**Why we recommend this movie:** {movie['reason']}")
            if details:
                st.write(f"**Director:** {details.get('Director', 'N/A')}")
                st.write(f"**Cast:** {details.get('Actors', 'N/A')}")
                st.write(f"**Genre:** {details.get('Genre', 'N/A')}")
                st.write(f"**IMDb Rating:** {details.get('imdbRating', 'N/A')}")
                st.write(f"**Plot:** {details.get('Plot', 'N/A')}")
            else:
                st.write("Detailed information not available.")
            st.markdown("---")  # Add a horizontal line between movies

# Sidebar for API key input
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
