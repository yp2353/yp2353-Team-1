from django.shortcuts import render, redirect

# from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
from .models import User
from django.contrib import messages
from .forms import SearchForm
from utils import get_spotify_token
import spotipy
from dashboard.models import Track

# Load variables from .env
load_dotenv()

# Create your views here.


def check_and_store_profile(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        user = request.user
        form = SearchForm()

        context = {
            "username": user.username,
            "user": user,
            "SearchForm": form,
            "track": Track.objects.filter(id=user.track_id).first() if user.track_id else None,
        }
        return render(request, "user_profile/user_profile.html", context)
    else:
        # No token, redirect to login again
        messages.error(
            request,
            "Check_and_store_profile failed, please try again later. User unavailable.",
        )
        return redirect("login:index")


def edit(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id", None)

        if user_id is not None:
            user = User.objects.filter(user_id=user_id).first()

            if not user:
                # User doesnt exist in database?
                messages.error(
                    request,
                    "Edit profile failed, please try again later. User unavailable.",
                )
                return redirect("login:index")

            context = {
                "username": user.username,
                "user": user,
            }
            return render(request, "user_profile/update_profile.html", context)

    messages.error(request, "Edit profile failed, please try again later.")
    return redirect("login:index")


def update(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id", None)

        if user_id is not None:
            user = User.objects.filter(user_id=user_id).first()

            if not user:
                # User doesnt exist in database?
                messages.error(
                    request,
                    "Update profile failed, please try again later. User unavailable.",
                )
                return redirect("login:index")

            bio = request.POST.get("user_bio", None)
            city = request.POST.get("user_city", None)

            if city:
                user.user_city = city
            if bio != user.user_bio:
                user.user_bio = bio
            user.save()

            return redirect("user_profile:profile_page")

    messages.error(request, "Edit profile failed, please try again later.")
    return redirect("login:index")


def search(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        user = request.user
        token_info = get_spotify_token(request)
        if token_info:
            sp = spotipy.Spotify(auth=token_info["access_token"])

            if request.method == "GET":
                form = SearchForm(request.GET)

                if form.is_valid():
                    search_query = form.cleaned_data["search_query"]
                    results = []
                    track_results = sp.search(q=search_query, type="track", limit=10)
                    for track in track_results["tracks"]["items"]:
                        track_info = {
                            "id": track["id"],
                            "name": track["name"],
                            "artists": ", ".join(
                                [artist["name"] for artist in track["artists"]]
                            ),
                            "album": track["album"]["name"],
                            "image": track["album"]["images"][0]["url"],
                            "release_date": track["album"]["release_date"],
                        }
                        results.append(track_info)

                else:
                    results = None

            else:
                form = SearchForm()
                results = None

            if user.track_id is not None:
                try:
                    track = Track.objects.get(id=user.track_id)

                except Track.DoesNotExist:
                    track = None
            else:
                track = None

            context = {
                "username": user.username,
                "user": user,
                "SearchForm": form,
                "results": results,
                "track": track,
            }
            return render(request, "user_profile/user_profile.html", context)

    messages.error(
        request,
        "Profile track search failed, please try again later.",
    )
    return redirect("login:index")


def changeTrack(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id", None)
        action = request.POST.get("action", None)

        if user_id is not None and action is not None:
            user = User.objects.filter(user_id=user_id).first()
            if not user:
                # User doesnt exist in database?
                messages.error(
                    request,
                    "Changing track failed, please try again later. User unavailable.",
                )
                return redirect("login:index")

            if action == "remove":
                user.track_id = None
                user.save()

            elif action == "add":
                track_id = request.POST.get("track_id", None)
                if track_id:
                    # Save track into database
                    existing = Track.objects.filter(id=track_id).first()

                    if not existing:
                        token_info = get_spotify_token(request)
                        if token_info:
                            sp = spotipy.Spotify(auth=token_info["access_token"])
                            track = sp.track(track_id)
                            audio_features = sp.audio_features([track_id])
                            audio_features = audio_features[0]

                            track_data = Track(
                                id=track_id,
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

                            track_data.save()

                        else:
                            messages.error(request, "Change track failed, please try again later. No token.")
                            return redirect("dashboard:index")
                    
                    user.track_id = track_id
                    user.save()

            return redirect("user_profile:profile_page")

    messages.error(request, "Change track failed, please try again later.")
    return redirect("dashboard:index")
