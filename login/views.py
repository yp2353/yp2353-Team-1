from django.shortcuts import render
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Create your views here.

def index(request):
    return render(request, 'login/index.html')

def dashboard(request):
    #scope = "user-top-read"
    #sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id='3e08d953068a4235a66288850e220e5f',client_secret='d518b3f60eb040f19120be4680868f00',redirect_uri='http://127.0.0.1:8000/login/dashboard',scope=scope))
    #top_tracks = sp.current_user_top_tracks(limit=10, offset=0, time_range="short_term")
    #context = {'top_tracks': top_tracks['items']}
    return render(request, 'login/dashboard.html')