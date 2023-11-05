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
import requests

# from dotenv import load_dotenv
import os

# from gensim.models import FastText
from utils import get_spotify_token, deduce_audio_vibe
from django.http import JsonResponse

# import boto3
# import tempfile
from user_profile.models import Vibe
from django.utils import timezone
import spacy

MAX_RETRIES = 2

# Load spaCy language model from the deployed location
nlp = spacy.load("dashboard/en_core_web_md/en_core_web_md-3.7.0")

""" AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")


s3 = boto3.client(
    "s3",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)


def load_model_from_s3():
    with tempfile.NamedTemporaryFile() as tmp:
        s3.download_file("vibecheck-storage", "cc.en.12.bin", tmp.name)
        model = FastText.load_fasttext_format(tmp.name)
    return model


# Uncomment for loading from S3
model = load_model_from_s3()"""


# Uncomment for manual loading
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

        # Get top tracks
        top_tracks = get_top_tracks(sp)

        # Get top artists and top genres based on artist
        top_artists, top_genres = get_top_artist_and_genres(sp)

        # Get recommendation based on tracks
        recommendedtracks = get_recommendations(sp, top_tracks)

        user_id = user_info["id"]
        current_time = timezone.now()
        midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        recent_vibe = Vibe.objects.filter(user_id=user_id, vibe_time__gte=midnight).first()
        if not recent_vibe:
            # If no vibe for this user today, save new row to Vibe database
            vibe_data = Vibe(
                user_id=user_id,
                vibe_time=timezone.now(),
                top_track=[track["id"]for track in top_tracks],
                top_artist=[artist["id"]for artist in top_artists],
                top_genre=top_genres,
                recommended_tracks=[track["id"]for track in recommendedtracks]
            )
            vibe_data.save()

        context = {
            "username": username,
            "top_tracks": top_tracks,
            "top_artists": top_artists,
            "top_genres": top_genres,
            "recommendedtracks": recommendedtracks,
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
                "artists": ", ".join(
                    [artist["name"] for artist in track["artists"]]
                ),
                "album": track["album"]["name"],
                "uri": track["uri"],
                "large_album_cover": track['album']['images'][0]['url'] if len(track['album']['images']) >= 1 else None,
                "medium_album_cover": track['album']['images'][1]['url'] if len(track['album']['images']) >= 2 else None,
                "small_album_cover": track['album']['images'][2]['url'] if len(track['album']['images']) >= 3 else None,
            }
        )
    return tracks


def get_top_artist_and_genres(sp):
    top_artists = sp.current_user_top_artists(limit=5, time_range='short_term')

    user_top_artists = []
    user_top_genres = set() #Set to store unique genres

    for artist in top_artists['items']:
        artist_info = {
            'name': artist['name'],
            'id': artist['id'],
            'image_url': artist['images'][0]['url'] if artist['images'] else None
        }
        user_top_artists.append(artist_info)
        user_top_genres.update(artist['genres']) 

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
                "artists": ", ".join(
                    [artist["name"] for artist in track["artists"]]
                ),
                "album": track["album"]["name"],
                "uri": track["uri"],
                "large_album_cover": track['album']['images'][0]['url'] if len(track['album']['images']) >= 1 else None,
                "medium_album_cover": track['album']['images'][1]['url'] if len(track['album']['images']) >= 2 else None,
                "small_album_cover": track['album']['images'][2]['url'] if len(track['album']['images']) >= 3 else None,
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
        current_time = timezone.now()
        time_difference = current_time - timezone.timedelta(hours=24)
        recent_vibe = Vibe.objects.filter(user_id=user_id, vibe_time__gte=time_difference).first()
        if recent_vibe and recent_vibe.user_audio_vibe:
            vibe_result = recent_vibe.user_audio_vibe
            if recent_vibe.user_lyrics_vibe:
                vibe_result += " " + recent_vibe.user_lyrics_vibe
            return JsonResponse({'result': vibe_result})
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

            # Find row in vibe database that is within 24 hours
            current_time = timezone.now()
            time_difference = current_time - timezone.timedelta(hours=24)
            recent_vibe = Vibe.objects.filter(user_id=user_id, vibe_time__gte=time_difference).first()
            if not recent_vibe:
                print("Error, vibe row should already exist when loaded dashboard!")
            else:
                recent_vibe.user_lyrics_vibe = lyric_vibe
                recent_vibe.user_audio_vibe = audio_vibe
                recent_vibe.recent_track = track_ids
                recent_vibe.user_acousticness = get_feature_average(audio_features_list, "acousticness")
                recent_vibe.user_danceability = get_feature_average(audio_features_list, "danceability")
                recent_vibe.user_energy = get_feature_average(audio_features_list, "energy")
                recent_vibe.user_valence = get_feature_average(audio_features_list, "valence")
            
                recent_vibe.save()
        else:
            vibe_result = "Null"

        return JsonResponse({"result": vibe_result})
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
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

    if lyrics_final_vibe:
        return audio_final_vibe, lyrics_final_vibe
    else:
        return audio_final_vibe


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
                    if vibe.lower() == "melancholic" or vibe.lower() == "melancholy":
                        lyrics_vibes.append("Sad")
                    else:
                        lyrics_vibes.append(vibe)
                    
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
    lyrics_constrain = [
        "Happy",
        "Sad",
        "Angry",
        "Anxious",
        "Content",
        "Excited",
        "Bored",
        "Nostalgic",
        "Frustrated",
        "Hopeful",
        "Afraid",
        "Confident",
        "Jealous",
        "Grateful",
        "Lonely",
        "Rebellious",
        "Relaxed",
        "Amused",
        "Curious",
        "Ashamed",
        "Sympathetic",
        "Disappointed",
        "Proud",
        "Guilty",
        "Enthusiastic",
        "Empathetic",
        "Shocked",
        "Calm",
        "Inspired",
        "Indifferent",
        "Romantic",
        "Tense",
        "Euphoric",
        "Restless",
        "Serene",
        "Sensual",
        "Reflective",
        "Playful",
        "Dark",
        "Optimistic",
        "Mysterious",
        "Seductive",
        "Regretful",
        "Detached",
    ]

    if lyrics_vibes:
        # avg_lyr_vibe = average_vector(lyrics_vibes, model)
        # final_lyr_vibe = vector_to_word(avg_lyr_vibe, model)
        # closest_emotion = find_closest_emotion(avg_lyr_vibe, model)
        closest_emotion = spacy_vectorize(lyrics_vibes, lyrics_constrain)
        return str(closest_emotion)
    else:
        return None


"""
def get_vector(word, model):
    # Get the word vector from the model.
    try:
        return model.wv[word]
    except KeyError:
        return np.zeros(model.vector_size)


def average_vector(words, model):
    # Compute the average vector for a list of words.
    vectors = [get_vector(word, model) for word in words]
    return np.mean(vectors, axis=0)


def vector_to_word(vector, model):
    # Find the closest word in the embedding for the given vector.
    # most_similar returns [(word, similarity score), ...]
    # We just want the word, so we pick [0][0]
    return model.wv.most_similar(positive=[vector], topn=1)[0][0] 


def find_closest_emotion(final_vibe, model):
    emotion_words = [
        "Happy", "Sad", "Angry", "Joyful", "Depressed", "Anxious", "Content",
        "Excited", "Bored", "Nostalgic", "Frustrated", "Hopeful", "Afraid",
        "Confident", "Jealous", "Grateful", "Lonely", "Overwhelmed", "Relaxed",
        "Amused", "Curious", "Ashamed", "Sympathetic", "Disappointed", "Proud",
        "Guilty", "Enthusiastic", "Empathetic", "Shocked", "Calm", "Inspired",
        "Disgusted", "Indifferent", "Romantic", "Surprised", "Tense", "Euphoric",
        "Melancholic", "Restless", "Serene", "Sensual"
    ]
    max_similarity = -1
    closest_emotion = None
    for word in emotion_words:
        word_vec = get_vector(word, model)
        similarity = cosine_similarity(final_vibe, word_vec)
        if similarity > max_similarity:
            max_similarity = similarity
            closest_emotion = word
    return closest_emotion


def cosine_similarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b)) """


def spacy_vectorize(vibe, constrain):
    vibe_string = " ".join(vibe)
    in_vocab_vibes = [token.text for token in nlp(vibe_string) if not token.is_oov]
    in_vocab_tokens = nlp(" ".join(in_vocab_vibes))

    if len(in_vocab_tokens) == 0:
        return None

    max_similarity = -1
    closest_emotion = None

    for word in constrain:
        similarity = nlp(word).similarity(in_vocab_tokens)
        if similarity > max_similarity:
            max_similarity = similarity
            closest_emotion = word

    return closest_emotion

def get_feature_average(list, feature):
    total = sum(track[feature] for track in list)
    average = total / len(list)
    return average