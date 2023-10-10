from django.shortcuts import render
import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Create your views here.

def index(request):
    return render(request, 'login/index.html')

def dashboard(request):
    #scope = "user-library-read"
    #sp = spotipy.Spotify(auth_manager=SpotifyOAuth(scope=scope))
    return render(request, 'login/dashboard.html')