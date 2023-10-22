from spotipy.oauth2 import SpotifyOAuth
from dotenv import load_dotenv
from decouple import config

# Load variables from .env
load_dotenv()

CLIENT_ID = config("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = config("SPOTIPY_CLIENT_SECRET")

REDIRECT_URI = "vcheck-env-1014.eba-megnbk6g.us-west-2.elasticbeanstalk.com/login/callback"

SCOPE = "user-top-read"
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
