from django.shortcuts import render, redirect
import spotipy
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter
import json
import shutil
import threading
from user_profile.views import check_and_store_profile

# from dotenv import load_dotenv
from utils import get_spotify_token, vibe_calc_threads, deduce_audio_vibe
from django.http import JsonResponse
from dashboard.models import TrackVibe
from user_profile.models import Vibe, UserTop
from django.utils import timezone
from django.contrib import messages

from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

from .vibe_calc import calculate_vibe_async


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

        # Get recent tracks
        recent_tracks = get_recent_tracks(sp)

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

        vibe_or_not = calculate_vibe(sp, midnight)
        # Possible values: already_loaded if vibe already calculated within today,
        # asyn_started if vibe calculation is started and still loading,
        # no_songs if user has 0 recent songs to analyze

        context = {
            "username": username,
            "top_tracks": top_tracks,
            "recent_tracks": recent_tracks,
            "top_artists": top_artists,
            "top_genres": top_genres,
            "recommendedtracks": recommendedtracks,
            "vibe_history": vibe_history,
            "iteratorMonth": months,
            "iteratorDay": range(0, 32),
            "currentYear": current_year,
            "midnight": midnight,
            "vibe_or_not": vibe_or_not,
        }

        extract_tracks(sp)

        return render(request, "dashboard/index.html", context)
    else:
        # No token, redirect to login again
        debug_info = f"Request: {request}"
        messages.error(
            request,
            f"Dashboard failed, please try again later. Debug info: {debug_info}",
        )
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


def get_recent_tracks(sp):
    recent_tracks = sp.current_user_recently_played(limit=10)
    tracks = []

    track_ids = [track["track"]["id"] for track in recent_tracks["items"]]
    audio_features_list = sp.audio_features(track_ids)

    existing_tracks = TrackVibe.objects.filter(track_id__in=track_ids)
    existing_tracks_dict = {track.track_id: track for track in existing_tracks}

    for track, audio_features in zip(recent_tracks["items"], audio_features_list):
        track_vibe = existing_tracks_dict.get(
            track["track"]["id"], TrackVibe(track_id=track["track"]["id"])
        )
        # Compute audio vibe for each track, doesn't matter if it was already in the database
        track_vibe.track_audio_vibe = deduce_audio_vibe([audio_features])
        track_vibe.save()
        display_lyrics_vibe = ""
        if track_vibe.track_lyrics_vibe is not None:
            display_lyrics_vibe = track_vibe.track_lyrics_vibe.capitalize()
        tracks.append(
            {
                "name": track["track"]["name"],
                "id": track["track"]["id"],
                "year": track["track"]["album"]["release_date"][:4],
                "artists": ", ".join(
                    [artist["name"] for artist in track["track"]["artists"]]
                ),
                "album": track["track"]["album"]["name"],
                "uri": track["track"]["uri"],
                "large_album_cover": track["track"]["album"]["images"][0]["url"]
                if len(track["track"]["album"]["images"]) >= 1
                else None,
                "medium_album_cover": track["track"]["album"]["images"][1]["url"]
                if len(track["track"]["album"]["images"]) >= 2
                else None,
                "small_album_cover": track["track"]["album"]["images"][2]["url"]
                if len(track["track"]["album"]["images"]) >= 3
                else None,
                "attributes": {
                    "Acousticness": audio_features["acousticness"] * 100,
                    "Danceability": audio_features["danceability"] * 100,
                    "Energy": audio_features["energy"] * 100,
                    "Instrumentalness": audio_features["instrumentalness"] * 100,
                    "Valence": audio_features["valence"] * 100,
                    "Loudness": (min(60, audio_features["loudness"] * -1) / 60) * 100,
                },
                "audio_vibe": track_vibe.track_audio_vibe.capitalize(),
                "lyrics_vibe": display_lyrics_vibe,
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
    recommendedtracks = []

    # Debug
    # return recommendedtracks

    try:
        recommendations = sp.recommendations(seed_tracks=seed_tracks, limit=5)
    except Exception:
        # No tracks as seed to recommend
        return recommendedtracks

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


def calculate_vibe(sp, midnight):
    # Check if user vibe already been calculated for today
    user_info = sp.current_user()
    user_id = user_info["id"]
    recent_vibe = Vibe.objects.filter(user_id=user_id, vibe_time__gte=midnight).first()

    if recent_vibe:
        return "already_loaded"
    # If vibe today is already in database, RETURN, do not schedule vibe calculation

    recent_tracks = sp.current_user_recently_played(limit=15)

    if not recent_tracks.get("items", []):
        return "no_songs"
    else:
        track_names = []
        track_artists = []
        track_ids = []

        for track in recent_tracks["items"]:
            track_names.append(track["track"]["name"])
            track_artists.append(track["track"]["artists"][0]["name"])
            track_ids.append(track["track"]["id"])

        audio_features_list = sp.audio_features(track_ids)

        # Schedule asynchronous vibe calculation
        # But first check if a thread is already running and calculating!
        if user_id not in vibe_calc_threads:
            vibe_thread = threading.Thread(
                target=calculate_vibe_async,
                args=(
                    track_names,
                    track_artists,
                    track_ids,
                    audio_features_list,
                    user_id,
                ),
            )
            vibe_thread.start()
            vibe_calc_threads[user_id] = vibe_thread

        return "asyn_started"


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


"""
# On huggingface spaces
def get_vector(word, model):
    # Get the word vector from the model.
    try:
        return model.wv[word]
    except KeyError:
        return np.zeros(model.vector_size)
"""


def get_task_status(request, midnight):
    token_info = get_spotify_token(request)

    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])
        user_info = sp.current_user()
        user_id = user_info["id"]

        # Check if there is a result in the database
        recent_vibe = Vibe.objects.filter(
            user_id=user_id, vibe_time__gte=midnight
        ).first()

        if recent_vibe and recent_vibe.user_audio_vibe:
            vibe_result = recent_vibe.user_audio_vibe
            if recent_vibe.user_lyrics_vibe:
                vibe_result += " " + recent_vibe.user_lyrics_vibe
            description = recent_vibe.description
            response_data = {
                "status": "SUCCESS",
                "result": vibe_result,
                "description": description,
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({"status": "PENDING"})

    else:
        # No token, redirect to login again
        messages.error(request, "Get_task_status failed, please try again later.")
        return redirect("login:index")


@require_POST
def upvote_track(request, track_id):
    track = get_object_or_404(TrackVibe, pk=track_id)
    track.upvote_count += 1
    track.save()
    return JsonResponse({"upvote_count": track.upvote_count})


@require_POST
def cancel_upvote_track(request, track_id):
    track = get_object_or_404(TrackVibe, pk=track_id)
    if track.upvote_count > 0:
        track.upvote_count -= 1
        track.save()
    return JsonResponse({"upvote_count": track.upvote_count})


@require_POST
def downvote_track(request, track_id):
    track = get_object_or_404(TrackVibe, pk=track_id)
    track.downvote_count += 1
    track.save()
    return JsonResponse({"downvote_count": track.downvote_count})


@require_POST
def cancel_downvote_track(request, track_id):
    track = get_object_or_404(TrackVibe, pk=track_id)
    if track.downvote_count >= 0:
        track.downvote_count -= 1
        track.save()
    return JsonResponse({"downvote_count": track.downvote_count})
