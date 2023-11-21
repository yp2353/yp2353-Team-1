from django.shortcuts import render, redirect
from utils import get_spotify_token
import spotipy
from django.contrib import messages
from user_profile.models import User, Vibe, UserFriendRelation
from django.db.models import Q


# Create your views here.
def other(request, other_user_id):
    token_info = get_spotify_token(request)

    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])
        user_info = sp.current_user()
        user_id = user_info["id"]
        # Pass username to navbar
        username = user_info["display_name"]

        if user_id == other_user_id:
            # Trying to view your own profile
            return redirect("user_profile:profile_page")

        user = User.objects.filter(user_id=user_id).first()
        other_user = User.objects.filter(user_id=other_user_id).first()
        if not user or not other_user:
            # One of the users dont exist in database, throw error
            messages.error(request, "Profile doesnt exist.")
            return redirect("dashboard:index")

        user_recent_vibe = (
            Vibe.objects.filter(user_id=user_id).order_by("-vibe_time").first()
        )
        other_recent_vibe = (
            Vibe.objects.filter(user_id=other_user_id).order_by("-vibe_time").first()
        )

        # Check if there's a friend request involving the user
        friend_request = UserFriendRelation.objects.filter(
            (Q(user1_id=user_id) & Q(user2_id=other_user_id))
            | (Q(user2_id=user_id) & Q(user1_id=other_user_id))
        ).first()

        # Determine the status of the friend request
        if friend_request:
            if (
                friend_request.user1_id.user_id == user_id
                and friend_request.status == "pending"
            ):
                # Current user sent friend request
                status = "user_sent_fr"
            else:
                status = friend_request.status
        else:
            status = "not_friend"

        context = {
            "username": username,
            "user": user,
            "user_recent_vibe": user_recent_vibe,
            "other_user": other_user,
            "other_recent_vibe": other_recent_vibe,
            "status": status,
            "default_image_path": "user_profile/blank_user_profile_image.jpeg",
        }

        return render(request, "view_profile/index.html", context)
    else:
        # No token, redirect to login again
        messages.error(request, "View_profile failed, please log in.")
        return redirect("login:index")


def process_fr(request):
    token_info = get_spotify_token(request)

    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        user_id = user_info["id"]

        if request.method == "POST":
            other_user_id = request.POST.get("other_user_id", None)
            action = request.POST.get("action", None)
            where_from = request.POST.get("where_from", None)

            if (
                other_user_id is not None
                and action is not None
                and where_from is not None
            ):
                try:
                    friend_request = UserFriendRelation.objects.filter(
                        (
                            Q(user1_id=user_id, user2_id=other_user_id)
                            | Q(user1_id=other_user_id, user2_id=user_id)
                        )
                    ).first()
                    if not friend_request:
                        raise UserFriendRelation.DoesNotExist

                    if action == "message":
                        # Redirect to private message
                        print("to be implemented...")

                    elif action == "cancel" or action == "unfriend":
                        friend_request.status = "not_friend"

                    elif action == "send":
                        # swaping a,b = b,a
                        # as in, user1 (the sender) should now be current user

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
                            (Q(user1_id=other_user_id)) & (Q(user2_id=user_id))
                        ).first()
                        friend_request.status = "friends"

                    elif action == "decline":
                        friend_request = UserFriendRelation.objects.filter(
                            (Q(user1_id=other_user_id)) & (Q(user2_id=user_id))
                        ).first()
                        friend_request.status = "not_friend"

                    friend_request.save()

                except UserFriendRelation.DoesNotExist:
                    if action == "send":
                        friend_request = UserFriendRelation(
                            user1_id=User.objects.get(user_id=user_id),
                            user2_id=User.objects.get(user_id=other_user_id),
                            status="pending",
                        )
                        friend_request.save()

                if where_from == "search_request_list":
                    return redirect("search:search_page")
                else:
                    # from "view_profile"
                    return redirect("view_profile:other", other_user_id=other_user_id)

        messages.error(request, "Process_fr form failed, please try again later.")
        return redirect("dashboard:index")

    else:
        # No token, redirect to login again
        messages.error(request, "Process_fr failed, please try again later.")
        return redirect("login:index")
