from spotipy.oauth2 import SpotifyOAuth
import os
import pandas as pd
from collections import Counter
from django.apps import apps
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# Comment the below line while working on your local machine
# REDIRECT_URI = (
#     "http://vcheck-env-1014.eba-megnbk6g.us-west-2.elasticbeanstalk.com/login/callback"
# )


# Uncomment the below line while working on your local machine
REDIRECT_URI = "http://127.0.0.1:8000/login/callback"

SCOPE = "user-top-read user-read-recently-played user-read-private"
sp_oauth = SpotifyOAuth(
    CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, scope=SCOPE, show_dialog=True
)

def get_spotify_token(request):
    token_info = request.session.get("token_info", None)
    if token_info and sp_oauth.is_token_expired(token_info):
        refresh_user_token = token_info.get("refresh_token")
        if refresh_user_token:
            new_token = sp_oauth.refresh_access_token(refresh_user_token)
            request.session["token_info"] = new_token
            return new_token
        else:
            # Error getting refresh token
            return None
    elif token_info:
        # Token still valid, return old token
        return token_info
    else:
        # Error getting saved token
        return None

def deduce_audio_vibe(audio_features_list):
    """
    Function to format the Spotify audio features and predict the most common mood
    using the provided model.

    Parameters:
    - audio_features_list: The audio features of the tracks as obtained from the Spotify API.

    Returns:
    - The most common mood from the predictions.
    """

    # Create a DataFrame from the list of audio features dictionaries
    spotify_data = pd.DataFrame(audio_features_list)

    # Rename 'duration_ms' to 'length' and normalize by dividing by the maximum value
    spotify_data.rename(columns={'duration_ms': 'length'}, inplace=True)
    if not spotify_data['length'].empty:
        max_length = spotify_data['length'].max()
        spotify_data['length'] = spotify_data['length'] / max_length

    # Reorder columns based on the model's expectations
    ordered_features = [
        'length',
        'danceability',
        'acousticness',
        'energy',
        'instrumentalness',
        'liveness',
        'valence',
        'loudness',
        'speechiness',
        'tempo',
        'key',
        'time_signature'
    ]

    # Ensure the DataFrame has all the required columns in the correct order
    spotify_data = spotify_data[ordered_features]

    # Define the mood dictionary
    mood_dict = {
        0: "Happy",
        1: "Sad",
        2: "Energetic",
        3: "Calm",
        4: "Anxious",
        5: "Cheerful",
        6: "Gloomy",
        7: "Content"
    }

    # Predict the moods using the model
    model = apps.get_app_config('dashboard').model
    pred = model.predict(spotify_data)

    # Find the most common mood prediction
    most_common_pred = Counter(pred).most_common(1)[0][0]
    audio_vibe = mood_dict.get(most_common_pred, "Unknown")

    return audio_vibe
