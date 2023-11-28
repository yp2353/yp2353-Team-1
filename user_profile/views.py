from django.shortcuts import render, redirect

# from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
from .models import User
from django.contrib import messages
from .forms import SearchForm
from utils import get_spotify_token
import spotipy

# Load variables from .env
load_dotenv()

# Create your views here.


def check_and_store_profile(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        user = request.user
        form = SearchForm()

        token_info = get_spotify_token(request)
        if token_info:
            sp = spotipy.Spotify(auth=token_info["access_token"])
        else:
            sp = None

        if user.track_id is not None and sp is not None:
            track = sp.track(user.track_id)
        else:
            track = None

        context = {
            "username": user.username,
            "user": user,
            "default_image_path": "user_profile/blank_user_profile_image.jpeg",
            "SearchForm": form,
            "track": track,
        }
        return render(request, "user_profile/user_profile.html", context)
    else:
        # No token, redirect to login again
        print("User Missing!!!!!")
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

            if user.track_id is not None and sp is not None:
                track = sp.track(user.track_id)
            else:
                track = None

            context = {
                "username": user.username,
                "user": user,
                "default_image_path": "user_profile/blank_user_profile_image.jpeg",
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
                    user.track_id = track_id
                    user.save()

            return redirect("user_profile:profile_page")

    messages.error(request, "Change track failed, please try again later.")
    return redirect("dashboard:index")
