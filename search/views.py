# from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import UsersearchForm
from utils import get_spotify_token
import spotipy
from user_profile.models import Vibe
from django.db.models import Q, OuterRef, Subquery, F
from django.contrib import messages

# Create your views here.
"""
for friends Relation User1 is sender and User2 is receiver
"""


def open_search_page(request, username=""):
    token_info = get_spotify_token(request)
    if token_info:
        form = UsersearchForm()
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        user_id = user_info["id"]
        # Pass username to navbar
        username = user_info["display_name"]

        request_list = get_req_list(user_id)

        friends = current_friend_list(user_id)
        latest_vibes = get_latest_vibes()

        all_users = latest_vibes.filter(
            user_id__in=[user.user_id for user in friends]
        ).values_list(
            "user_id",
            "user_lyrics_vibe",
            "user_audio_vibe",
            flat=False,
        )

        print(all_users)

        context = {
            "username": username,
            "current_user_id": user_id,
            "UsersearchForm": form,
            "request_list": request_list,
            "friends": friends,
            "default_image_path": "user_profile/blank_user_profile_image.jpeg",
            "recent_vibe": zip(friends, all_users),
        }

        return render(request, "search/search.html", context)
    else:
        # No token, redirect to login again
        messages.error(request, "Open_search_page failed, please try again later.")
        return redirect("login:index")


def get_req_list(user_id):
    from user_profile.models import UserFriendRelation

    request_list = []
    received_request = UserFriendRelation.objects.filter(
        (Q(user2_id=user_id)) & Q(status="pending")
    )

    for req in received_request:
        request_list.append(req.user1_id)

    return request_list


def user_search(request):
    from user_profile.models import User

    if request.user.is_authenticated:
        user = request.user

        current_user_id = user.user_id
        # Pass username to navbar
        current_username = user.username

        request_list = get_req_list(current_user_id)

        if request.method == "GET":
            form = UsersearchForm(request.GET)

            if form.is_valid():
                query = form.cleaned_data
                query_username = query["username"]

                user_search_filter = {"username__icontains": query_username}

                response = User.objects.filter(**user_search_filter)
                results = []
                for entry in response:
                    form.username = query_username
                    query_user_id = entry.user_id
                    if query_user_id == current_user_id:
                        # You should not be able to search yourself
                        continue

                    results.append({"user": entry})
            else:
                results = None
        else:
            form = UsersearchForm()
            results = None
    else:
        # No token, redirect to login again
        messages.error(request, "User_search failed, please try again later.")
        return redirect("login:index")

    context = {
        "username": current_username,
        "current_user_id": current_user_id,
        "results": results,
        "UsersearchForm": form,
        "request_list": request_list,
        "friends": current_friend_list(current_user_id),
        "default_image_path": "user_profile/blank_user_profile_image.jpeg",
    }
    return render(request, "search/search.html", context)


def current_friend_list(user_id):
    from user_profile.models import UserFriendRelation

    friendship_list = UserFriendRelation.objects.filter(
        (Q(user1_id=user_id) | Q(user2_id=user_id)) & Q(status="friends")
    )

    friends = []
    for friend in friendship_list:
        if friend.user2_id.user_id == user_id:
            friends.append(friend.user1_id)
        else:
            friends.append(friend.user2_id)

    return friends


def get_latest_vibes():
    # Get the most recent vibe for each user
    # Subquery to get the latest vibe_time for each user
    latest_vibe_times = (
        Vibe.objects.filter(user_id=OuterRef("user_id"))
        .order_by("-vibe_time")
        .values("vibe_time")[:1]
    )

    # Filter Vibe objects to only get those matching the latest vibe_time for each user
    latest_vibes = Vibe.objects.annotate(
        latest_vibe_time=Subquery(latest_vibe_times)
    ).filter(vibe_time=F("latest_vibe_time"))

    return latest_vibes
