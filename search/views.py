# from django.http import JsonResponse
from django.shortcuts import render, redirect
from .forms import UsersearchForm
from utils import get_spotify_token
import spotipy
from user_profile.models import User, UserFriendRelation
from django.db.models import Q

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
        print(type(user_id))
        request_list = []
        received_request = UserFriendRelation.objects.filter(
            (Q(user2_id=user_id)) & Q(status="pending")
        )

        for req in received_request:
            if req.user1_id == user_id:
                sender_id = req.user1_id
            else:
                sender_id = req.user1_id
            # sender = User.objects.filter(Q(user_id=sender_id)).first()
            print(sender_id)
            request_list.append(sender_id)

        context = {
            "UsersearchForm": form,
            "request_list": request_list,
            "friends": current_friend_list(user_id),
        }

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
            sp = spotipy.Spotify(auth=token_info["access_token"])

            user_info = sp.current_user()
            current_user_id = user_info["id"]
            
            if form.is_valid():
                query = form.cleaned_data
                username = query["username"]

                user_search_filter = {"username": username}

                response = User.objects.filter(**user_search_filter)
                results = []
                for entry in response:
                    user_id = entry.user_id
                    # Check if there's a friend request involving the user
                    friend_request = UserFriendRelation.objects.filter(
                        Q(user1_id=user_id) | Q(user2_id=user_id)
                    ).first()
                    # Determine the status of the friend request
                    if friend_request:
                        status = friend_request.status
                    else:
                        status = "not_friend"

                    results.append({"user": entry, "status": status})
                    form.username = username
            else:
                results = None
        else:
            form = UsersearchForm()
            results = None
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")
    context = {
        "results": results, 
        "UsersearchForm": form,
        "friends": current_friend_list(current_user_id),
        }
    return render(request, "search/search.html", context)


def process_friend_request(request, friend_user_id):
    token_info = get_spotify_token(request)

    if token_info:
        action = request.GET.get("action")
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        user_id = user_info["id"]

        try:
            friend_request = UserFriendRelation.objects.filter(
                (
                    Q(user1_id=user_id, user2_id=friend_user_id)
                    | Q(user1_id=friend_user_id, user2_id=user_id)
                )
            ).first()
            if not friend_request:
                raise UserFriendRelation.DoesNotExist

            if action == "cancel":
                friend_request.status = "cancle_request"

            elif action == "unfriend":
                friend_request.status = "not_friend"

            elif action == "send":
                if friend_request.user1_id.user_id != user_id:
                    (
                        friend_request.user1_id.user_id,
                        friend_request.user2_id.user_id,
                    ) = (
                        friend_request.user2_id.user_id,
                        friend_request.user1_id.user_id,
                    )

            # swaping a,b = b,a
            elif action == "accept":
                friend_request = UserFriendRelation.objects.filter(
                    (Q(user1_id=friend_user_id)) & (Q(user2_id=user_id))
                ).first()
                friend_request.status = "friends"

            elif action == "decline":
                friend_request = UserFriendRelation.objects.filter(
                    (Q(user1_id=friend_user_id)) & (Q(user2_id=user_id))
                ).first()
                friend_request.status = "decline"

            friend_request.save()

        except UserFriendRelation.DoesNotExist:
            if action == "send":
                friend_request = UserFriendRelation(
                    user1_id=User.objects.get(user_id=user_id),
                    user2_id=User.objects.get(user_id=friend_user_id),
                    status="pending",
                )
                friend_request.save()

        # print('message -> Friend request processed successfully')
        # response_data = {'message': 'Friend request processed successfully'}
        # return JsonResponse(response_data)

        return open_search_page(request)

    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")


def current_friend_list(user_id):
    friendship_list = UserFriendRelation.objects.filter(
        (Q(user1_id=user_id) | Q(user2_id=user_id)) & Q(status="friends")
    )

    friends = []
    print(friendship_list)
    for friend in friendship_list:
        if friend.user2_id.user_id == user_id:
            friends.append(friend.user1_id)
        else:
            friends.append(friend.user2_id)

    return friends
