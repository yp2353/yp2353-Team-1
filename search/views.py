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
            "UsersearchForm": form,
            "request_list": request_list,
            "friends": current_friend_list(user_id),
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

                    # Check if there's a friend request involving the user
                    friend_request = UserFriendRelation.objects.filter(
                        (Q(user1_id=current_user_id) & Q(user2_id=query_user_id))
                        | (Q(user2_id=current_user_id) & Q(user1_id=query_user_id))
                    ).first()

                    # Determine the status of the friend request
                    if friend_request:
                        if (
                            friend_request.user1_id.user_id == current_user_id
                            and friend_request.status == "pending"
                        ):
                            # Current user sent friend request
                            status = "user_sent_fr"
                        else:
                            status = friend_request.status
                    else:
                        status = "not_friend"

                    results.append({"user": entry, "status": status})
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
        "results": results,
        "UsersearchForm": form,
        "request_list": request_list,
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

            if action == "cancel" or action == "unfriend":
                friend_request.status = "not_friend"

            elif action == "send":
                # swaping a,b = b,a
                # as in, user1 (the sender) should now be current user

                # TROUBLE: GOT A FRIEND REQ FROM ANOTHER USER AND I CHANGE LINK TO SEND
                if friend_request.user1_id.user_id != user_id:
                    print("before", friend_request.user1_id)
                    (
                        friend_request.user1_id,
                        friend_request.user2_id,
                    ) = (
                        friend_request.user2_id,
                        friend_request.user1_id,
                    )
                friend_request.status = "pending"
                print("after", friend_request.user1_id)

            elif action == "accept":
                friend_request = UserFriendRelation.objects.filter(
                    (Q(user1_id=friend_user_id)) & (Q(user2_id=user_id))
                ).first()
                friend_request.status = "friends"

            elif action == "decline":
                friend_request = UserFriendRelation.objects.filter(
                    (Q(user1_id=friend_user_id)) & (Q(user2_id=user_id))
                ).first()
                friend_request.status = "not_friend"

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
        messages.error(
            request, "Process_friend_request failed, please try again later."
        )
        return redirect("login:index")


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
