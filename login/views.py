from django.shortcuts import render, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.http import HttpResponse
from django.contrib.sessions.models import Session


# Create your views here.
CLIENT_ID = '056b638f0a6f414ab93b5e70f4bfcab4'
CLIENT_SECRET = 'cb83a02e10fc4c6695ffeaba44e1c9be'
REDIRECT_URI = 'http://127.0.0.1:8000/login/callback'
SCOPE = "user-top-read"
sp_oauth = SpotifyOAuth(CLIENT_ID, CLIENT_SECRET, REDIRECT_URI, scope=SCOPE, show_dialog=True)

def index(request):
    return render(request, 'login/index.html')

def authenticate_spotify(request):
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

def callback(request):
    auth_code = request.GET.get('code', None)
    if auth_code:
        token_info = sp_oauth.get_access_token(auth_code)

        # Store token_info in your database or session for future API requests
        request.session['token_info'] = token_info

        # Redirect to the dashboard page after successful authentication
        return redirect('login:dashboard')
    else:
        # Handle error or unauthorized access
        return HttpResponse("Authorization error occurred")
    
def dashboard(request):
    token_info = request.session.get('token_info', None)

    if token_info:
        # Initialize Spotipy with the stored access token
        sp = spotipy.Spotify(auth=token_info['access_token'])
        
        # Fetch the user's top tracks (limit=10 for example, adjust as needed)
        top_tracks = sp.current_user_top_tracks(limit=10, time_range='medium_term')
        
        # Extract relevant information from the API response
        tracks = []
        for track in top_tracks['items']:
            tracks.append({
                'name': track['name'],
                'artists': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'uri': track['uri']
            })

        # Pass the top tracks data to the template
        context = {
            'tracks': tracks
        }

        # Render the dashboard template with the top tracks data
        return render(request, 'login/dashboard.html', context)
    else:
        # Handle authentication error, redirect to login page or show an error message
        return HttpResponse("Error!")
    
    # Handle dashboard logic, retrieve data, etc.
    #return render(request, 'login/dashboard.html')

def logout_view(request):
    # Clear the user's session data
    request.session.clear()
    return redirect('login:index')

""" def authenticate_spotify(request):
    # Define the desired scope
    scope = "user-top-read"
    
    # Initialize SpotifyOAuth with your client credentials and redirect URI
    sp_auth = SpotifyOAuth(scope=scope, client_id='3e08d953068a4235a66288850e220e5f', client_secret='d518b3f60eb040f19120be4680868f00', redirect_uri='https://127.0.0.1:8000/login/dashboard')
    
    # Generate the authorization URL and redirect the user to Spotify for authentication
    auth_url = sp_auth.get_authorize_url()
    return redirect(auth_url)

def dashboard(request):
    request = authenticate_spotify(request)
    # Check if the authorization code is present in the request
    if 'code' in request.GET:
        # Obtain the authorization code from the request
        auth_code = request.GET.get('code')
        
        # Use the authorization code to get the access token and refresh token
        auth_token = sp_auth.get_access_token(auth_code)
        
        # Initialize Spotify client with the obtained access token
        sp = spotipy.Spotify(auth=auth_token['access_token'])
        
        # Get user's top tracks
        top_tracks = sp.current_user_top_tracks(limit=10, offset=0, time_range="short_term")
        
        # Pass top_tracks data to the template in the context dictionary
        context = {'top_tracks': top_tracks['items']}
        
        # Render the dashboard template with top_tracks data
        return render(request, 'login/dashboard.html', context)
    
    # Handle cases where there is no authorization code (error handling)
    else:
        # Handle the error (e.g., display an error message)
        return HttpResponse("Authorization error occurred")

from django.shortcuts import render, redirect
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from django.http import HttpResponse
# Define the desired scope and SpotifyOAuth details outside of the functions
# Ideally, get these values from Django's settings or environment variables
CLIENT_ID = 'YOUR_CLIENT_ID'
CLIENT_SECRET = 'YOUR_CLIENT_SECRET'
REDIRECT_URI = 'http://127.0.0.1:8000/login/dashboard'
SCOPE = "user-top-read"
sp_auth = SpotifyOAuth(scope=SCOPE, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI)
def index(request):
    return render(request, 'login/index.html')
def authenticate_spotify(request):
    # Generate the authorization URL and redirect the user to Spotify for authentication
    auth_url = sp_auth.get_authorize_url()
    return redirect(auth_url)
def dashboard(request):
    # Check if the authorization code is present in the request
    if 'code' in request.GET:
        # Obtain the authorization code from the request
        auth_code = request.GET.get('code')
        # Use the authorization code to get the access token and refresh token
        auth_token = sp_auth.get_access_token(auth_code)
        # Initialize Spotify client with the obtained access token
        sp = spotipy.Spotify(auth=auth_token['access_token'])
        # Get user's top tracks
        top_tracks = sp.current_user_top_tracks(limit=10, offset=0, time_range="short_term")
        # Pass top_tracks data to the template in the context dictionary
        context = {'top_tracks': top_tracks['items']}
        # Render the dashboard template with top_tracks data
        return render(request, 'login/dashboard.html', context)
    else:
        # Handle the error (e.g., display an error message)
        return HttpResponse("Authorization error occurred") """