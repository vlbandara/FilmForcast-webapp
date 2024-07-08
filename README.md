# FilmForcast 🎬

FilmForcast is a personalized movie recommendation application that suggests films based on your daily experiences and mood. Utilizing the power of AI, it analyzes your day and provides tailored movie recommendations to complement your current state of mind.

## Features

- **Day Analysis**: Describe your day, and FilmForcast will analyze your mood, activities, interests, and emotional needs.
- **Personalized Recommendations**: Receive five movie suggestions tailored to your current state, complete with reasons for each recommendation.
- **Movie Details**: View comprehensive information about each recommended movie, including poster, cast, director, genre, and IMDb rating.
- **Favorites List**: Save your favorite movie recommendations for future reference.
- **Watch History**: Keep track of the movies you've watched, including the date you marked them as watched.
- **Movie Insights**: Gain insights into your watching habits with visualizations of your genre preferences.

## Technologies Used

- Streamlit: For the web application framework
- Google's Generative AI (Gemini 1.5 Pro): For day analysis and movie recommendations
- OMDB API: For fetching detailed movie information
- Plotly: For data visualization
- Pandas: For data manipulation and analysis

## Setup and Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/filmforcast.git
   cd filmforcast
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   - Create a `.streamlit/secrets.toml` file in the project root
   - Add your API keys:
     ```
     GEMINI_API_KEY = "your_gemini_api_key"
     OMDB_API_KEY = "your_omdb_api_key"
     ```

4. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

## Usage

1. Enter a detailed description of your day in the text area provided.
2. Click "Get Personalized Movie Recommendations" to receive your tailored suggestions.
3. Explore the recommended movies, their details, and the reasons for each recommendation.
4. Add movies to your favorites or mark them as watched to build your personal movie profile.
5. View your movie insights to understand your watching patterns.

## Contributing

Contributions to FilmForcast are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Streamlit for the awesome web app framework
- Google for the Generative AI capabilities
- OMDB for the comprehensive movie database

---

Created with ❤️ by Vinodh Lahiru
