from django.shortcuts import render, redirect
import spotipy
from utils import get_spotify_token

# Create your views here.

def index(request):
    token_info = get_spotify_token(request)
    #token_info = request.session.get('token_info', None)

    if token_info:
        # Initialize Spotipy with stored access token
        sp = spotipy.Spotify(auth=token_info['access_token'])

        top_tracks = sp.current_user_top_tracks(limit=10, time_range='short_term')
        tracks = []
        for track in top_tracks['items']:
            tracks.append({
                'name': track['name'],
                'artists': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'uri': track['uri']
            })
        context = {
            'tracks': tracks
        }

        return render(request, 'dashboard/index.html', context)
    else:
        #No token, redirect to login again
        #ERROR MESSAGE HERE?
        return redirect('login:index')
    
def logout(request):
    # Clear Django session data
    request.session.clear()
    return redirect('login:index')