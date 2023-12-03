from django.shortcuts import render, redirect
import spotipy
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter
import threading

# from dotenv import load_dotenv
from utils import get_spotify_token, vibe_calc_threads
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

        user_recent_tracks = sp.current_user_recently_played(limit=10)

        vibe_or_not = calculate_vibe(sp, midnight, user_recent_tracks)
        # Possible values: already_loaded if vibe already calculated within today,
        # asyn_started if vibe calculation is started and still loading,
        # no_songs if user has 0 recent songs to analyze

        hour_data, day_data = day_and_hour_info(user_recent_tracks)

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
            "midnight": midnight,
            "vibe_or_not": vibe_or_not,
            "hour_data": hour_data,
            "day_data": day_data,
        }

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
    top_tracks = sp.current_user_top_tracks(limit=5, time_range="short_term")
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


def calculate_vibe(sp, midnight, recent_tracks):
    # Check if user vibe already been calculated for today
    user_info = sp.current_user()
    user_id = user_info["id"]
    recent_vibe = Vibe.objects.filter(user_id=user_id, vibe_time__gte=midnight).first()

    if recent_vibe:
        return "already_loaded"
    # If vibe today is already in database, RETURN, do not schedule vibe calculation

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


def day_and_hour_info(recent_tracks):
    if not recent_tracks.get("items", []):
        return None, None
    
    timestamps = [track["played_at"] for track in recent_tracks["items"]]
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
        autosize=True,
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
        autosize=True,
    )


    hour_json = hour_fig.to_json()
    day_json = day_fig.to_json()


    return hour_json, day_json


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
            recent_tracks = get_recent_tracks(sp, recent_vibe.recent_track)
            response_data = {
                "status": "SUCCESS",
                "result": vibe_result,
                "description": description,
                "recent_tracks": recent_tracks,
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({"status": "PENDING"})

    else:
        # No token, redirect to login again
        messages.error(request, "Get_task_status failed, please try again later.")
        return redirect("login:index")


def get_recent_tracks(sp, track_ids):
    # In theory, all tracks in track_ids should exist in database already!
    existing_tracks = TrackVibe.objects.filter(track_id__in=track_ids)

    final_tracks = []

    for track in existing_tracks:
        audio_features = sp.audio_features([track.track_id])
        track_info = sp.track(track.track_id)

        if not audio_features or not track_info:
            continue

        audio_features = audio_features[0]
        
        final_tracks.append(
            {
                "name": track_info["name"],
                "id": track_info["id"],
                "year": track_info["album"]["release_date"][:4],
                "artists": ", ".join(
                    [artist["name"] for artist in track_info["artists"]]
                ),
                "album": track_info["album"]["name"],
                "uri": track_info["uri"],
                "large_album_cover": track_info["album"]["images"][0]["url"] if len(track_info["album"]["images"]) >= 1 else None,
                "medium_album_cover": track_info["album"]["images"][1]["url"] if len(track_info["album"]["images"]) >= 2 else None,
                "small_album_cover": track_info["album"]["images"][2]["url"] if len(track_info["album"]["images"]) >= 3 else None,
                "attributes": {
                    "Acousticness": audio_features["acousticness"] * 100,
                    "Danceability": audio_features["danceability"] * 100,
                    "Energy": audio_features["energy"] * 100,
                    "Instrumentalness": audio_features["instrumentalness"] * 100,
                    "Valence": audio_features["valence"] * 100,
                    "Loudness": (min(60, audio_features["loudness"] * -1) / 60) * 100,
                },
                "audio_vibe": track.track_audio_vibe.capitalize(),
                "lyrics_vibe": track.track_lyrics_vibe if track.track_lyrics_vibe else "",
            }
        )
    
    return final_tracks


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
