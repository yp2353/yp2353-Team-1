from django.shortcuts import render, redirect
import spotipy
import threading

# from dotenv import load_dotenv
from utils import get_spotify_token, vibe_calc_threads
from django.http import JsonResponse
from dashboard.models import TrackVibe, Track, Artist
from user_profile.models import Vibe, UserTop
from django.utils import timezone
from django.contrib import messages

from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404

from .vibe_calc import calculate_vibe_async


def index(request):
    token_info = get_spotify_token(request)

    if token_info:
        # Initialize Spotipy with stored access token
        sp = spotipy.Spotify(auth=token_info["access_token"])

        # Pass username to navbar
        user_info = sp.current_user()
        username = user_info["display_name"]

        user_id = user_info["id"]
        current_time = timezone.now().astimezone(timezone.utc)
        midnight = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        recent_top = UserTop.objects.filter(user_id=user_id, time__gte=midnight).first()
        if not recent_top:
            # If no top info for this user today, get and save new row to UserTop database

            # Get top tracks and recommendation based on tracks
            top_tracks = sp.current_user_top_tracks(limit=5, time_range="short_term")
            top_track_ids = [track["id"] for track in top_tracks["items"]]

            recommendedtracks_ids = []
            if top_track_ids:
                save_track_info(top_tracks["items"], sp.audio_features(top_track_ids))
            
                recommendedtracks = sp.recommendations(seed_tracks=top_track_ids, limit=5)
                recommendedtracks_ids = [track["id"] for track in recommendedtracks["tracks"]]
                save_track_info(recommendedtracks["tracks"], sp.audio_features(recommendedtracks_ids))
                
            # Get top artists and top genres based on artist
            top_artists = sp.current_user_top_artists(limit=5, time_range="short_term")
            top_artists_ids = [artist["id"] for artist in top_artists["items"]]
            save_artist_info(top_artists["items"])
            top_genres = get_genres(top_artists["items"])
            
            top_data = UserTop(
                user_id=user_id,
                time=current_time,
                top_track=top_track_ids,
                top_artist=top_artists_ids,
                top_genre=top_genres,
                recommended_tracks=recommendedtracks_ids,
            )
            top_data.save()

            # Final data for context
            top_tracks = Track.objects.filter(id__in=top_track_ids)
            recommendedtracks = Track.objects.filter(id__in=recommendedtracks_ids)
            top_artists = Artist.objects.filter(id__in=top_artists_ids)

        else:
            #Already have top data today
            top_tracks = Track.objects.filter(id__in=recent_top.top_track)
            recommendedtracks = Track.objects.filter(id__in=recent_top.recommended_tracks)
            top_artists = Artist.objects.filter(id__in=recent_top.top_artist)
            top_genres = recent_top.top_genre

        # Check if user vibe already been calculated for today
        recent_vibe = Vibe.objects.filter(user_id=user_id, vibe_time__gte=midnight).first()
        if recent_vibe:
            # Vibe already calculated within today
            vibe_or_not = "already_loaded"
        else:
            user_recent_tracks = sp.current_user_recently_played(limit=10)
            recent_tracks_ids = [item["track"]["id"] for item in user_recent_tracks["items"]]
            recent_tracks_list = [item["track"] for item in user_recent_tracks["items"]]
            if recent_tracks_ids:
                recent_tracks_audio = sp.audio_features(recent_tracks_ids)
                save_track_info(recent_tracks_list, recent_tracks_audio)
                calculate_vibe(user_id, recent_tracks_list, recent_tracks_audio)
                vibe_or_not = "asyn_started"
            else:
                # Uf user has 0 recent songs to analyze
                vibe_or_not = "no_songs"


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
            "midnight": midnight,
            "vibe_or_not": vibe_or_not,
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


def save_track_info(tracks_list, audio_features_list):
    data_list = []

    for track, audio_features in zip(tracks_list, audio_features_list):
        track_data = Track(
            id=track["id"],
            name=track["name"],
            popularity=track["popularity"],
            album_name=track["album"]["name"],
            album_release_date=track["album"]["release_date"],
            album_images_large=track["album"]["images"][0]["url"]
            if len(track["album"]["images"]) >= 1
            else None,
            album_images_small=track["album"]["images"][2]["url"]
            if len(track["album"]["images"]) >= 3
            else None,
            artist_names=[artist["name"] for artist in track["artists"]],
            artist_ids=[artist["id"] for artist in track["artists"]],
            acousticness=audio_features["acousticness"],
            danceability=audio_features["danceability"],
            energy=audio_features["energy"],
            instrumentalness=audio_features["instrumentalness"],
            loudness=audio_features["loudness"],
            speechiness=audio_features["speechiness"],
            valence=audio_features["valence"],
        )
        data_list.append(track_data)
    
    Track.objects.bulk_create(data_list)


def save_artist_info(artist_list):
    data_list = []

    for artist in artist_list:
        artist_info = Artist(
            id=artist["id"],
            followers=artist["followers"]["total"],
            genres=artist["genres"],
            image=artist["images"][0]["url"] if artist["images"] else None,
            name=artist["name"],
            popularity=artist["popularity"],
        )
        data_list.append(artist_info)
    
    Artist.objects.bulk_create(data_list)


def get_genres(top_artists):
    user_top_genres = set()  # Set to store unique genres

    for artist in top_artists:
        user_top_genres.update(artist["genres"])

    return list(user_top_genres)


def calculate_vibe(user_id, recent_tracks_list, recent_tracks_audio):
    track_names = []
    track_artists = []
    track_ids = []

    for track in recent_tracks_list:
        track_names.append(track["name"])
        track_artists.append(track["artists"][0]["name"])
        track_ids.append(track["id"])

    # Schedule asynchronous vibe calculation
    # But first check if a thread is already running and calculating!
    if user_id not in vibe_calc_threads:
        vibe_thread = threading.Thread(
            target=calculate_vibe_async,
            args=(
                track_names,
                track_artists,
                track_ids,
                recent_tracks_audio,
                user_id,
            ),
        )
        vibe_thread.start()
        vibe_calc_threads[user_id] = vibe_thread


def logout(request):
    # Clear Django session data
    request.session.clear()
    return redirect("login:index")


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
    if request.user.is_authenticated:
        user = request.user
        user_id = user.user_id

        # Check if there is a result in the database
        recent_vibe = Vibe.objects.filter(
            user_id=user_id, vibe_time__gte=midnight
        ).first()

        if recent_vibe and recent_vibe.user_audio_vibe:
            vibe_result = recent_vibe.user_audio_vibe
            if recent_vibe.user_lyrics_vibe:
                vibe_result += " " + recent_vibe.user_lyrics_vibe
            description = recent_vibe.description
            recent_tracks = get_recent_tracks(recent_vibe.recent_track)
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
        messages.error(
            request,
            "Get_task_status failed, please try again later.",
        )
        return redirect("login:index")


def get_recent_tracks(track_ids):
    # In theory, all tracks in track_ids should exist in database already!
    existing_tracks = TrackVibe.objects.filter(track_id__in=track_ids)

    final_tracks = []

    for track in existing_tracks:
        try:
            track_row = Track.objects.get(id=track.track_id)

        except Track.DoesNotExist:
            continue

        final_tracks.append(
            {
                "name": track_row.name,
                "id": track_row.id,
                "year": track_row.album_release_date[:4],
                "artists": ", ".join(track_row.artist_names),
                "album": track_row.album_name,
                "large_album_cover": track_row.album_images_large,
                "attributes": {
                    "Acousticness": track_row.acousticness * 100,
                    "Danceability": track_row.danceability * 100,
                    "Energy": track_row.energy * 100,
                    "Instrumentalness": track_row.instrumentalness * 100,
                    "Valence": track_row.valence * 100,
                    "Loudness": (min(60, track_row.loudness * -1) / 60) * 100,
                },
                "audio_vibe": track.track_audio_vibe.capitalize(),
                "lyrics_vibe": track.track_lyrics_vibe
                if track.track_lyrics_vibe
                else "",
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
