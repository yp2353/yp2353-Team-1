from spotipy.oauth2 import SpotifyOAuth
import os
import pandas as pd
from dotenv import load_dotenv

# Load variables from .env
load_dotenv()

CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")

# REDIRECT_URI = 'http://vcheck-env-1014.eba-megnbk6g.us-west-2.elasticbeanstalk.com/login/callback'
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

def format_audio_features(track_features):
    """
    Optimized function to format the Spotify audio features for model prediction.

    Parameters:
    - track_features: The audio features of the track as obtained from the Spotify API.

    Returns:
    - A formatted pandas DataFrame suitable for making predictions with the loaded model.
    """
    # Directly create the DataFrame with the desired column order and renaming
    ordered_features = [
        ('popularity', 1),  # Assuming popularity is a static placeholder
        ('duration_ms', 'length'),  # Rename 'duration_ms' to 'length'
        'danceability', 'acousticness', 'energy', 'instrumentalness',
        'liveness', 'valence', 'loudness', 'speechiness', 'tempo',
        'key', 'time_signature'
    ]

    # Prepare a dictionary for renaming and column order
    rename_dict = {orig: new if isinstance(new, str) else orig
                   for orig, new in ordered_features}
    columns_order = [new if isinstance(new, str) else orig
                     for orig, new in ordered_features]

    # Select, rename, and reorder columns in one go
    spotify_data = pd.DataFrame(track_features).rename(columns=rename_dict)[columns_order]

    return spotify_data