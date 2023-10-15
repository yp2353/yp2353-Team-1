from spotipy.oauth2 import SpotifyOAuth

#CLIENT_ID = ''
#CLIENT_SECRET = ''
REDIRECT_URI = 'http://vcheck-env-1014.eba-megnbk6g.us-west-2.elasticbeanstalk.com/login/callback'
SCOPE = "user-top-read"
sp_oauth = SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, scope=SCOPE, show_dialog=True)

def get_spotify_token(request):
    token_info = request.session.get('token_info', None)
    if token_info and sp_oauth.is_token_expired(token_info):
        refresh_user_token = token_info.get('refresh_token')
        if refresh_user_token:
            new_token = sp_oauth.refresh_access_token(refresh_user_token)
            request.session['token_info'] = new_token
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
