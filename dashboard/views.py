from django.shortcuts import render, redirect
import spotipy
from utils import get_spotify_token


# Create your views here.

def index(request):
    token_info = get_spotify_token(request)
    # token_info = request.session.get('token_info', None)

    if token_info:
        # Initialize Spotipy with stored access token
        sp = spotipy.Spotify(auth=token_info['access_token'])

        top_tracks = sp.current_user_top_tracks(limit=5, time_range='short_term')
        # Fetch top tracks and artists for the currently authenticated user
        #top_artists = sp.current_user_top_artists(limit=2)

        # Extract seed tracks, artists, and genres
        seed_tracks = [track['id'] for track in top_tracks['items']]
        #seed_artists = [artist['id'] for artist in top_artists['items']]
        #seed_genres = list(set(genre for artist in top_artists['items'] for genre in artist['genres']))
        recommendations = sp.recommendations(seed_tracks=seed_tracks)


        tracks = []
        for track in top_tracks["items"]:
            tracks.append({
                'name': track['name'],
                'artists': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'uri': track['uri']
            })
        
        recommendedtracks = []
        for track in recommendations["tracks"]:
            recommendedtracks.append({
                'name': track['name'],
                'artists': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'uri': track['uri']
            })

        context = {
            'tracks': tracks,
            'recommendedtracks': recommendedtracks
        }

        return render(request, 'dashboard/index.html', context)
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect('login:index')


def logout(request):
    # Clear Django session data
    request.session.clear()
    return redirect('login:index')
