# from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import UsersearchForm
from utils import get_spotify_token
import spotipy
from user_profile.models import User, UserFriendRelation
from django.db.models import Q
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

        context = {
            "username": username,
            "current_user_id": user_id,
            "UsersearchForm": form,
            "request_list": request_list,
            "friends": current_friend_list(user_id),
            "default_image_path": "user_profile/blank_user_profile_image.jpeg",
        }

        return render(request, "search/search.html", context)
    else:
        # No token, redirect to login again
        messages.error(request, "Open_search_page failed, please try again later.")
        return redirect("login:index")


def get_req_list(user_id):
    request_list = []
    received_request = UserFriendRelation.objects.filter(
        (Q(user2_id=user_id)) & Q(status="pending")
    )

    for req in received_request:
        request_list.append(req.user1_id)

    return request_list


def user_search(request):
    token_info = get_spotify_token(request)
    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        current_user_id = user_info["id"]
        # Pass username to navbar
        current_username = user_info["display_name"]

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
