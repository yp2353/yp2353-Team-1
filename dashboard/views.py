from django.shortcuts import render, redirect
import spotipy
from utils import get_spotify_token
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter
import json
import shutil
import lyricsgenius
import openai
import time



# Create your views here.

def index(request):
    token_info = get_spotify_token(request)
    # token_info = request.session.get('token_info', None)

    if token_info:
        # Initialize Spotipy with stored access token
        sp = spotipy.Spotify(auth=token_info['access_token'])

        top_tracks = sp.current_user_top_tracks(limit=5, time_range='short_term')
        # Fetch top tracks and artists for the currently authenticated user
        # top_artists = sp.current_user_top_artists(limit=2)

        # Extract seed tracks, artists, and genres
        seed_tracks = [track['id'] for track in top_tracks['items']]
        # seed_artists = [artist['id'] for artist in top_artists['items']]
        # seed_genres = list(set(genre for artist in top_artists['items'] for genre in artist['genres']))
        recommendations = sp.recommendations(seed_tracks=seed_tracks)
        track_names = [track['name'] for track in top_tracks['items']]

        check_vibe(track_names)

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

        extract_tracks(sp)

        return render(request, 'dashboard/index.html', context)
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect('login:index')


def logout(request):
    # Clear Django session data
    request.session.clear()
    return redirect('login:index')


def extract_tracks(sp):
    recently_played = sp.current_user_recently_played()
    timestamps = [track['played_at'] for track in recently_played['items']]
    # Convert to datetime and extract hour and day
    hours_of_day = [datetime.fromisoformat(ts[:-1]).hour for ts in timestamps]
    days_of_week = [datetime.fromisoformat(ts[:-1]).weekday() for ts in timestamps]
    hours_count = Counter(hours_of_day)
    days_count = Counter(days_of_week)

    # Plot by Hour of Day
    hour_fig = go.Figure()
    hour_fig.add_trace(go.Bar(x=list(hours_count.keys()), y=list(hours_count.values()), marker_color='blue'))
    hour_fig.update_layout(title='Listening Patterns by Hour of Day',
                           xaxis_title='Hour of Day',
                           yaxis_title='Number of Tracks Played',
                           xaxis=dict(tickvals=list(range(24)), ticktext=list(range(24))),
                           plot_bgcolor='black',  # Background color of the plotting area
                           paper_bgcolor='black',  # Background color of the entire paper
                           font=dict(color='white')
                                     )


    # Plot by Day of Week
    days_labels = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_fig = go.Figure()
    day_fig.add_trace(go.Bar(x=days_labels, y=[days_count[i] for i in range(7)], marker_color='green'))

    # Update the layout
    day_fig.update_layout(
        title='Listening Patterns by Day of Week',
        xaxis_title='Day of Week',
        yaxis_title='Number of Tracks Played',
        plot_bgcolor='black',  # Background color of the plotting area
        paper_bgcolor='black',  # Background color of the entire paper
        font=dict(color='white')  # To make the font color white for better visibility
    )

    # Save as HTML

    hour_json = hour_fig.to_json()
    day_json = day_fig.to_json()

    # You can save this JSON data to a file or use some other method to transfer it to your webpage.
    with open('hour_data.json', 'w') as f:
        json.dump(hour_json, f)

    with open('day_data.json', 'w') as f:
        json.dump(day_json, f)

    shutil.move("hour_data.json", "login/static/login/hour_data.json")
    shutil.move("day_data.json", "login/static/login/day_data.json")


def check_vibe(track_names):
    genius = lyricsgenius.Genius("")
    lyrics_data = {}

    for track in track_names:
        song = genius.search_song(track)
        if song:
            lyrics_data[track] = song.lyrics

    openai.api_key = ''

    for track, lyrics in lyrics_data.items():
        short_lyrics = lyrics[:2048]
        print("hola")
        try:
            print("Processing song:", track)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user",
                     "content": f"Analyze the vibe of the song based on these lyrics and return only the 3 top vibes separated by commas: '{short_lyrics}'"}
                ])
            vibe = response.choices[0].message['content'].strip()
            print(f"The vibe for {track} is: {vibe}")
        except Exception as e:
            print(f"Error processing the vibe for {track}: {e}")

            # Ensure you don't exceed the rate limits
        time.sleep(20)



