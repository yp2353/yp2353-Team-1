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
from dotenv import load_dotenv
import os
import numpy as np
from gensim.models import FastText
from django.http import JsonResponse

# Load variables from .env
load_dotenv()

# Create your views here.
model = FastText.load_fasttext_format('dashboard/cc.en.300.bin')


def index(request):
    token_info = get_spotify_token(request)
    # token_info = request.session.get('token_info', None)

    if token_info:
        # Initialize Spotipy with stored access token
        sp = spotipy.Spotify(auth=token_info['access_token'])

        top_tracks = sp.current_user_top_tracks(limit=10, time_range='short_term')

        # Extract seed tracks, artists, and genres
        seed_tracks = [track['id'] for track in top_tracks['items']]
        recommendations = sp.recommendations(seed_tracks=seed_tracks[:4])


        #EXTRA STUFF
        # top_artists = sp.current_user_top_artists(limit=2)
        # seed_artists = [artist['id'] for artist in top_artists['items']]
        # seed_genres = list(set(genre for artist in top_artists['items'] for genre in artist['genres']))


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


def calculate_vibe(request):
    #Check if user vibe exists already for today

    token_info = get_spotify_token(request)

    if token_info:
        sp = spotipy.Spotify(auth=token_info['access_token'])

        recent_tracks = sp.current_user_recently_played(limit=15)

        track_names = []
        track_artists = []
        track_ids = []

        for track in recent_tracks['items']:
            track_names.append(track['track']['name'])
            track_artists.append(track['track']['artists'][0]['name'])
            track_ids.append(track['track']['id'])

        #IF TESTING WITH TOP TRACKS INSTEAD OF RECENT
        """ top_tracks = sp.current_user_top_tracks(limit=10, time_range='short_term')
        for track in top_tracks['items']:
            track_names.append(track['name'])
            track_artists.append(track['artists'][0]['name'])
            track_ids.append(track['id']) """
        
        if recent_tracks:
            audio_features_list = sp.audio_features(track_ids)
            vibe_result = check_vibe(track_names, track_artists, track_ids, audio_features_list)

            #Add user vibe to vibe database
        else:
            vibe_result = "Null"

        return JsonResponse({'result': vibe_result})
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


def check_vibe(track_names, track_artists, track_ids, audio_features_list):
    
    lyrics_vibes = deduce_lyrics(track_names, track_artists, track_ids)

    audio_vibes = deduce_audio(audio_features_list)
    #CURRENTLY USING deduce_audio, REPLACE WITH MOOD MODEL.
    #SAVE INTO TRACK DATABASE AS WELL WITH ID?


    return vectorize(lyrics_vibes, audio_vibes)


def deduce_lyrics(track_names, track_artists, track_ids):
    genius = lyricsgenius.Genius(os.getenv('GENIUS_TOKEN'))

    lyrics_vibes = []

    # CHECK TRACK DATABASE BASED ON ID, ADD TRACK VIBE TO LYRICS_VIBES IF ALREADY IN DATABASE!!!

    lyrics_data = {}
    for track, artist, id in zip(track_names, track_artists, track_ids):
        #SKIP TRACKS ALRDY IN DATABASE!!!

        query = f'"{track}" "{artist}"'
        song = genius.search_song(query)
        if song and song.title.lower() == track.lower() and song.artist.lower() == artist.lower():
                lyrics_data[(track, artist, id)] = song.lyrics

    openai.api_key = os.getenv('OPEN_AI_TOKEN')

    for (track, artist, id), lyrics in lyrics_data.items():
        short_lyrics = lyrics[:2048]
        try:
            print(f"Processing song. Track: {track}, Artist: {artist}, ID: {id}")
            print(f"Lyrics: {short_lyrics[:200]}")
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user",
                     "content": f"You are a mood analyzer that can only return a single word. Based on these song lyrics, return a single word that matches this song's mood: '{short_lyrics}'"}
                ])
            vibe = response.choices[0].message['content'].strip()
            checkLength = vibe.split()
            if len(checkLength) == 1:
                lyrics_vibes.append(vibe)
            print(f"The vibe for {track} is: {vibe}")

            # INSERT VIBE HERE INTO TRACK DATABASE!!!!!

        except Exception as e:
            print(f"Error processing the vibe for {track}: {e}")
    
    return lyrics_vibes



def vectorize(lyrics_vibes, audio_vibes):
    #TESTING, to be deleted
    #final_vibe_multiplied = np.multiply(avg_vibe, avg_emotion)
    #final_vibe_su = np.add(avg_vibe, avg_emotion)
    #dot_product = np.dot(avg_vibe, avg_emotion)
    #b_norm_squared = np.dot(avg_emotion, avg_emotion)
    #projection = (dot_product / b_norm_squared) * avg_emotion
    #normalized_multiplied = vector_to_word(normalize(final_vibe_multiplied), model)
    #normalized_vibe_sum = vector_to_word(normalize(final_vibe_su), model)
    #normalized_projection = vector_to_word(normalize(projection), model)
    # print("the final vibe is: ", normalized_multiplied, normalized_vibe_sum, normalized_projection,
    #" avg output: ", final_emotion, final_vibe)

    avg_aud_vibe = average_vector(audio_vibes, model)
    final_aud_vibe = vector_to_word(avg_aud_vibe, model)

    if lyrics_vibes:
        avg_lyr_vibe = average_vector(lyrics_vibes, model)
        final_lyr_vibe = vector_to_word(avg_lyr_vibe, model)
        print("The final lyric audio vibe is:", str(final_aud_vibe) + " " + str(final_lyr_vibe))
        return str(final_aud_vibe) + " " + str(final_lyr_vibe)
    else:
        print("The final audio vibe is:", str(final_aud_vibe))
        return str(final_aud_vibe)
    

def get_vector(word, model):
    """Get the word vector from the model."""
    try:
        return model.wv[word]
    except KeyError:
        return np.zeros(model.vector_size)


def average_vector(words, model):
    """Compute the average vector for a list of words."""
    vectors = [get_vector(word, model) for word in words]
    return np.mean(vectors, axis=0)


def vector_to_word(vector, model):
    """Find the closest word in the embedding for the given vector."""
    # most_similar returns [(word, similarity score), ...]
    # We just want the word, so we pick [0][0]
    return model.wv.most_similar(positive=[vector], topn=1)[0][0]



def deduce_audio(audio_features_list):
    num_tracks = len(audio_features_list)

    valence = sum([track["valence"] for track in audio_features_list]) / num_tracks
    energy = sum([track["energy"] for track in audio_features_list]) / num_tracks
    danceability = sum([track["danceability"] for track in audio_features_list]) / num_tracks
    acousticness = sum([track["acousticness"] for track in audio_features_list]) / num_tracks
    instrumentalness = sum([track["instrumentalness"] for track in audio_features_list]) / num_tracks
    tempo = sum([track["tempo"] for track in audio_features_list]) / num_tracks
    loudness = sum([track["loudness"] for track in audio_features_list]) / num_tracks

    emotions = []

    # High-level categories based on valence and energy
    if valence > 0.5 and energy > 0.5:
        emotions.append("Joyful")
    elif valence > 0.5 and energy <= 0.5:
        emotions.append("Content")
    elif valence <= 0.5 and energy > 0.5:
        emotions.append("Frustrated")
    else:
        emotions.append("Sad")

    # Refine based on other attributes
    if danceability > 0.7:
        emotions.append("Dancey")

    if acousticness > 0.7:
        emotions.append("Nostalgic")

    if instrumentalness > 0.7:
        emotions.append("Reflective")

    if tempo > 120:  # 120 BPM is taken as a generic "fast" threshold
        emotions.append("Energetic")
    else:
        emotions.append("Relaxed")

    if loudness > -5:  # -5 dB is taken as a generic "loud" threshold
        emotions.append("Intense")


    return emotions


def normalize(vector):
    #Used for testing only for now
    magnitude = np.linalg.norm(vector)
    if magnitude == 0:
        return vector
    return vector / magnitude
