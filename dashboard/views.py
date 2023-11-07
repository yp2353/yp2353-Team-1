from django.shortcuts import render, redirect
import spotipy
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter
import json
import shutil
import lyricsgenius
import openai
import time
import numpy as np
from gradio_client import Client
import re
import threading
from user_profile.views import check_and_store_profile

# from dotenv import load_dotenv
import os

from utils import get_spotify_token, deduce_audio_vibe
from django.http import JsonResponse

from user_profile.models import Vibe, UserTop
from django.utils import timezone
from dashboard.models import EmotionVector

MAX_RETRIES = 2

client = Client("https://alfredo273-vibecheck-fasttext.hf.space/--replicas/zt2rw/")

# Uncomment for manual loading
# from gensim.models import FastText
# model = FastText.load_fasttext_format("dashboard/cc.en.32.bin")


def index(request):
    token_info = get_spotify_token(request)
    # token_info = request.session.get('token_info', None)

    if token_info:
        # Initialize Spotipy with stored access token
        sp = spotipy.Spotify(auth=token_info["access_token"])

        # Pass username to navbar
        user_info = sp.current_user()
        username = user_info["display_name"]

        def run_check_and_store_profile():
            check_and_store_profile(request)

        # Create a thread to run the function
        thread = threading.Thread(target=run_check_and_store_profile)

        # Start the thread
        thread.start()

        # Get top tracks
        top_tracks = get_top_tracks(sp)

        # Get top artists and top genres based on artist
        top_artists, top_genres = get_top_artist_and_genres(sp)

        # Get recommendation based on tracks
        recommendedtracks = get_recommendations(sp, top_tracks)

        user_id = user_info["id"]
        current_time = timezone.now().astimezone(timezone.utc)
        midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        recent_top = UserTop.objects.filter(user_id=user_id, time__gte=midnight).first()
        if not recent_top:
            # If no top info for this user today, save new row to UserTop database
            top_data = UserTop(
                user_id=user_id,
                time=current_time,
                top_track=[track["id"] for track in top_tracks],
                top_artist=[artist["id"] for artist in top_artists],
                top_genre=top_genres,
                recommended_tracks=[track["id"] for track in recommendedtracks],
            )
            top_data.save()

        current_year = current_time.year
        vibe_history = Vibe.objects.filter(
            user_id=user_id, vibe_time__year=current_year
        ).values("vibe_time", "user_audio_vibe", "user_lyrics_vibe")
        months = [
            {"number": 0, "short_name": "", "long_name": ""},
            {"number": 1, "short_name": "J", "long_name": "January"},
            {"number": 2, "short_name": "F", "long_name": "February"},
            {"number": 3, "short_name": "M", "long_name": "March"},
            {"number": 4, "short_name": "A", "long_name": "April"},
            {"number": 5, "short_name": "M", "long_name": "May"},
            {"number": 6, "short_name": "J", "long_name": "June"},
            {"number": 7, "short_name": "J", "long_name": "July"},
            {"number": 8, "short_name": "A", "long_name": "August"},
            {"number": 9, "short_name": "S", "long_name": "September"},
            {"number": 10, "short_name": "O", "long_name": "October"},
            {"number": 11, "short_name": "N", "long_name": "November"},
            {"number": 12, "short_name": "D", "long_name": "December"},
        ]

        context = {
            "username": username,
            "top_tracks": top_tracks,
            "top_artists": top_artists,
            "top_genres": top_genres,
            "recommendedtracks": recommendedtracks,
            "vibe_history": vibe_history,
            "iteratorMonth": months,
            "iteratorDay": range(0, 32),
            "currentYear": current_year,
        }

        extract_tracks(sp)

        return render(request, "dashboard/index.html", context)
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")


def get_top_tracks(sp):
    top_tracks = sp.current_user_top_tracks(limit=10, time_range="short_term")
    tracks = []
    for track in top_tracks["items"]:
        tracks.append(
            {
                "name": track["name"],
                "id": track["id"],
                "artists": ", ".join([artist["name"] for artist in track["artists"]]),
                "album": track["album"]["name"],
                "uri": track["uri"],
                "large_album_cover": track["album"]["images"][0]["url"]
                if len(track["album"]["images"]) >= 1
                else None,
                "medium_album_cover": track["album"]["images"][1]["url"]
                if len(track["album"]["images"]) >= 2
                else None,
                "small_album_cover": track["album"]["images"][2]["url"]
                if len(track["album"]["images"]) >= 3
                else None,
            }
        )
    return tracks


def get_top_artist_and_genres(sp):
    top_artists = sp.current_user_top_artists(limit=5, time_range="short_term")

    user_top_artists = []
    user_top_genres = set()  # Set to store unique genres

    for artist in top_artists["items"]:
        artist_info = {
            "name": artist["name"],
            "id": artist["id"],
            "image_url": artist["images"][0]["url"] if artist["images"] else None,
        }
        user_top_artists.append(artist_info)
        user_top_genres.update(artist["genres"])

    return user_top_artists, list(user_top_genres)


def get_recommendations(sp, top_tracks):
    seed_tracks = [track["id"] for track in top_tracks[:5]]
    recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=5)

    recommendedtracks = []
    for track in recommendations["tracks"]:
        recommendedtracks.append(
            {
                "name": track["name"],
                "id": track["id"],
                "artists": ", ".join([artist["name"] for artist in track["artists"]]),
                "album": track["album"]["name"],
                "uri": track["uri"],
                "large_album_cover": track["album"]["images"][0]["url"]
                if len(track["album"]["images"]) >= 1
                else None,
                "medium_album_cover": track["album"]["images"][1]["url"]
                if len(track["album"]["images"]) >= 2
                else None,
                "small_album_cover": track["album"]["images"][2]["url"]
                if len(track["album"]["images"]) >= 3
                else None,
            }
        )

    return recommendedtracks


def calculate_vibe(request):
    token_info = get_spotify_token(request)

    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])

        # Check if user vibe already been calculated for today
        user_info = sp.current_user()
        user_id = user_info["id"]
        current_time = timezone.now().astimezone(timezone.utc)
        midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        recent_vibe = Vibe.objects.filter(
            user_id=user_id, vibe_time__gte=midnight
        ).first()
        if recent_vibe and recent_vibe.user_audio_vibe:
            vibe_result = recent_vibe.user_audio_vibe
            if recent_vibe.user_lyrics_vibe:
                vibe_result += " " + recent_vibe.user_lyrics_vibe
            return JsonResponse({"result": vibe_result})
        # Skips having to perform vibe calculations below

        recent_tracks = sp.current_user_recently_played(limit=15)

        track_names = []
        track_artists = []
        track_ids = []

        for track in recent_tracks["items"]:
            track_names.append(track["track"]["name"])
            track_artists.append(track["track"]["artists"][0]["name"])
            track_ids.append(track["track"]["id"])

        # IF TESTING WITH TOP TRACKS INSTEAD OF RECENT
        """ top_tracks = sp.current_user_top_tracks(limit=10, time_range='short_term')
        for track in top_tracks['items']:
            track_names.append(track['name'])
            track_artists.append(track['artists'][0]['name'])
            track_ids.append(track['id']) """

        if track_ids:
            audio_features_list = sp.audio_features(track_ids)
            audio_vibe, lyric_vibe = check_vibe(
                track_names, track_artists, track_ids, audio_features_list
            )
            vibe_result = audio_vibe
            if lyric_vibe:
                vibe_result += " " + lyric_vibe

            current_time = timezone.now().astimezone(timezone.utc)
            vibe_data = Vibe(
                user_id=user_id,
                vibe_time=current_time,
                user_lyrics_vibe=lyric_vibe,
                user_audio_vibe=audio_vibe,
                recent_track=track_ids,
                user_acousticness=get_feature_average(
                    audio_features_list, "acousticness"
                ),
                user_danceability=get_feature_average(
                    audio_features_list, "danceability"
                ),
                user_energy=get_feature_average(audio_features_list, "energy"),
                user_valence=get_feature_average(audio_features_list, "valence"),
            )
            vibe_data.save()
        else:
            vibe_result = "Null"

        return JsonResponse({"result": vibe_result})
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")
        return redirect("login:index")


def logout(request):
    # Clear Django session data
    request.session.clear()
    return redirect("login:index")


def extract_tracks(sp):
    recently_played = sp.current_user_recently_played()
    timestamps = [track["played_at"] for track in recently_played["items"]]
    # Convert to datetime and extract hour and day
    hours_of_day = [datetime.fromisoformat(ts[:-1]).hour for ts in timestamps]
    days_of_week = [datetime.fromisoformat(ts[:-1]).weekday() for ts in timestamps]
    hours_count = Counter(hours_of_day)
    days_count = Counter(days_of_week)

    # Plot by Hour of Day
    hour_fig = go.Figure()
    hour_fig.add_trace(
        go.Bar(
            x=list(hours_count.keys()),
            y=list(hours_count.values()),
            marker_color="blue",
        )
    )
    hour_fig.update_layout(
        title="Listening Patterns by Hour of Day",
        xaxis_title="Hour of Day",
        yaxis_title="Number of Tracks Played",
        xaxis=dict(tickvals=list(range(24)), ticktext=list(range(24))),
        plot_bgcolor="black",  # Background color of the plotting area
        paper_bgcolor="black",  # Background color of the entire paper
        font=dict(color="white"),
    )

    # Plot by Day of Week
    days_labels = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    day_fig = go.Figure()
    day_fig.add_trace(
        go.Bar(x=days_labels, y=[days_count[i] for i in range(7)], marker_color="green")
    )

    # Update the layout
    day_fig.update_layout(
        title="Listening Patterns by Day of Week",
        xaxis_title="Day of Week",
        yaxis_title="Number of Tracks Played",
        plot_bgcolor="black",  # Background color of the plotting area
        paper_bgcolor="black",  # Background color of the entire paper
        font=dict(color="white"),  # To make the font color white for better visibility
    )

    # Save as HTML

    hour_json = hour_fig.to_json()
    day_json = day_fig.to_json()

    # You can save this JSON data to a file or use some other method to transfer it to your webpage.
    with open("hour_data.json", "w") as f:
        json.dump(hour_json, f)

    with open("day_data.json", "w") as f:
        json.dump(day_json, f)

    shutil.move("hour_data.json", "login/static/login/hour_data.json")
    shutil.move("day_data.json", "login/static/login/day_data.json")


def check_vibe(track_names, track_artists, track_ids, audio_features_list):
    audio_final_vibe = deduce_audio_vibe(audio_features_list)

    lyrics_vibes = deduce_lyrics(track_names, track_artists, track_ids)
    lyrics_final_vibe = lyrics_vectorize(lyrics_vibes)

    if not lyrics_final_vibe:
        lyrics_final_vibe = None

    return audio_final_vibe, lyrics_final_vibe


def deduce_lyrics(track_names, track_artists, track_ids):
    genius = lyricsgenius.Genius(os.getenv("GENIUS_CLIENT_ACCESS_TOKEN"))

    lyrics_vibes = []

    # CHECK TRACK DATABASE BASED ON ID, ADD TRACK VIBE TO LYRICS_VIBES IF ALREADY IN DATABASE!!!

    lyrics_data = {}
    for track, artist, id in zip(track_names, track_artists, track_ids):
        # SKIP TRACKS ALRDY IN DATABASE!!!
        query = f'"{track}" "{artist}"'
        song = genius.search_song(query)
        if song:
            # Genius song object sometimes has trailing space, so need to strip
            geniusTitle = song.title.lower().replace("\u200b", " ").strip()
            geniusArtist = song.artist.lower().replace("\u200b", " ").strip()
            if geniusTitle == track.lower() and geniusArtist == artist.lower():
                print("Inputting lyrics..")
                lyrics_data[(track, artist, id)] = song.lyrics

    openai.api_key = os.getenv("OPEN_AI_TOKEN")

    for (track, artist, id), lyrics in lyrics_data.items():
        short_lyrics = lyrics[:2048]
        retries = 0
        while retries < MAX_RETRIES:
            try:
                print(f"Processing song. Track: {track}, Artist: {artist}, ID: {id}")
                print(f"Lyrics: {short_lyrics[:200]}")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {
                            "role": "user",
                            "content": f"You are a mood analyzer that can only return a single word. Based on these song lyrics, return a single word that matches this song's mood: '{short_lyrics}'",
                        },
                    ],
                    request_timeout=5,
                )
                vibe = response.choices[0].message["content"].strip()
                checkLength = vibe.split()
                if len(checkLength) == 1:
                    lyrics_vibes.append(vibe.lower())

                    # INSERT VIBE HERE INTO TRACK DATABASE!!!!!
                print(f"The vibe for {track} is: {vibe}")

                break
            except Exception as e:
                print(f"Error processing the vibe for {track}: {e}")
                retries += 1

            if retries >= MAX_RETRIES:
                print(f"Retries maxed out processing the vibe for {track}.")
                break
            else:
                time.sleep(1)

    return lyrics_vibes


def lyrics_vectorize(lyrics_vibes):
    if lyrics_vibes:
        for i in lyrics_vibes:
            print("Lyrics vibes: " + i)
        avg_lyr_vibe = average_vector(lyrics_vibes)
        closest_emotion = find_closest_emotion(avg_lyr_vibe)
        return str(closest_emotion)
    else:
        return None


def string_to_vector(str):
    clean = re.sub(r"[\[\]\n\t]", "", str)
    clean = clean.split()
    clean = [float(e) for e in clean]
    return clean


"""
# On huggingface spaces
def get_vector(word, model):
    # Get the word vector from the model.
    try:
        return model.wv[word]
    except KeyError:
        return np.zeros(model.vector_size)
"""


def average_vector(words):
    # Compute the average vector for a list of words.
    vectors = []
    for word in words:
        str_vector = client.predict("get_vector", word, api_name="/predict")
        vector = string_to_vector(str_vector)
        vectors.append(vector)

    return np.mean(vectors, axis=0)


def find_closest_emotion(final_vibe):
    emotion_words = [
        "happy",
        "sad",
        "angry",
        "anxious",
        "content",
        "excited",
        "bored",
        "nostalgic",
        "frustrated",
        "hopeful",
        "afraid",
        "confident",
        "jealous",
        "grateful",
        "lonely",
        "rebellious",
        "relaxed",
        "amused",
        "curious",
        "ashamed",
        "sympathetic",
        "disappointed",
        "proud",
        "enthusiastic",
        "empathetic",
        "shocked",
        "calm",
        "inspired",
        "indifferent",
        "romantic",
        "tense",
        "euphoric",
        "restless",
        "serene",
        "sensual",
        "reflective",
        "playful",
        "dark",
        "optimistic",
        "mysterious",
        "seductive",
        "regretful",
        "detached",
        "melancholic",
    ]

    max_similarity = -1
    closest_emotion = None
    for word in emotion_words:
        word_vec = get_emotion_vector(word)
        similarity = cosine_similarity(final_vibe, word_vec)
        if similarity > max_similarity:
            max_similarity = similarity
            closest_emotion = word
    return closest_emotion


def cosine_similarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))


def get_feature_average(list, feature):
    total = sum(track[feature] for track in list)
    average = total / len(list)
    return average


def get_emotion_vector(input_emotion):
    input_emotion = input_emotion.lower()
    vector_str = EmotionVector.objects.filter(emotion=input_emotion).first()

    if not vector_str:
        # We should always get vector string stored in our database,
        # but if somehow is not in database..
        vector_str = client.predict("get_vector", input_emotion, api_name="/predict")
    else:
        vector_str = vector_str.vector

    return string_to_vector(vector_str)
