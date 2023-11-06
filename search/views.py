from django.shortcuts import render, redirect
from .forms import UsersearchForm
from utils import get_spotify_token
import spotipy
from user_profile.models import User, FriendRequest
from django.db.models import Q

# Create your views here.


def open_search_page(request):
    token_info = get_spotify_token(request)
    if token_info:
        form = UsersearchForm()
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        user_id = user_info["id"]
        request_list = []
        received_request = FriendRequest.objects.filter(Q(receiver=user_id))
        for req in received_request:
            sender_id = req.sender.user_id
            sender = User.objects.filter(Q(user_id=sender_id)).first()
            request_list.append(sender)

        context = {"UsersearchForm": form, "request_list": request_list}
        print(request_list)
        return render(request, "search/search.html", context)
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")


def user_search(request):
    token_info = get_spotify_token(request)
    if token_info:
        if request.method == "GET":
            form = UsersearchForm(request.GET)
            if form.is_valid():
                query = form.cleaned_data
                username = query["username"]

                user_search_filter = {"username": username}

                response = User.objects.filter(**user_search_filter)
                results = []
                for entry in response:
                    user_id = entry.user_id
                    # Check if there's a friend request involving the user
                    friend_request = FriendRequest.objects.filter(
                        Q(sender=user_id) | Q(receiver=user_id)
                    ).first()
                    # Determine the status of the friend request
                    if friend_request:
                        status = friend_request.status
                    else:
                        status = "no_friend"

                    results.append({"user": entry, "status": status})
            else:
                results = None
        else:
            form = UsersearchForm()
            results = None
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")
    context = {"results": results, "UsersearchForm": form}
    return render(request, "search/search.html", context)


def process_friend_request(request):
    token_info = get_spotify_token(request)
    print("Profile User Check Started")
    if token_info:
        return open_search_page(request)

    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")
