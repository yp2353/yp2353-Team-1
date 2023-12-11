from django.utils import timezone
from django.shortcuts import render, redirect
from django.contrib import messages
from user_profile.models import User, Vibe, UserFriendRelation, UserTop
from chatroom.models import RoomModel
from django.db.models import Q
from dashboard.models import Track, Artist


# Create your views here.
def compare(request, other_user_id):
    if request.user.is_authenticated:
        user_info = request.user
        user_id = user_info.user_id
        # Pass username to navbar
        username = user_info.username

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
        user_top_items = (
            UserTop.objects.filter(user_id=user_id).order_by("-time").first()
        )
        other_top_items = (
            UserTop.objects.filter(user_id=other_user_id).order_by("-time").first()
        )

        info = {
            "user": {
                "recent_vibe": user_recent_vibe,
                "fav_track": Track.objects.filter(id=user.track_id).first()
                if user.track_id
                else None,
                "recent_tracks": Track.objects.filter(
                    id__in=user_recent_vibe.recent_track[:5]
                )
                if user_recent_vibe and user_recent_vibe.recent_track
                else None,
                "top_tracks": Track.objects.filter(id__in=user_top_items.top_track[:5])
                if user_top_items and user_top_items.top_track
                else None,
                "top_artists": Artist.objects.filter(
                    id__in=user_top_items.top_artist[:5]
                )
                if user_top_items and user_top_items.top_artist
                else None,
                "top_genres": user_top_items.top_genre[:5] if user_top_items else None,
                "iteratorRecentTracks": range(
                    min(5, len(user_recent_vibe.recent_track))
                )
                if user_recent_vibe
                else [],
                "iteratorTopTracks": range(min(5, len(user_top_items.top_track)))
                if user_top_items
                else [],
                "iteratorTopArtists": range(min(5, len(user_top_items.top_artist)))
                if user_top_items
                else [],
            },
            "other": {
                "recent_vibe": other_recent_vibe,
                "fav_track": Track.objects.filter(id=other_user.track_id).first()
                if other_user.track_id
                else None,
                "recent_tracks": Track.objects.filter(
                    id__in=other_recent_vibe.recent_track[:5]
                )
                if other_recent_vibe and other_recent_vibe.recent_track
                else None,
                "top_tracks": Track.objects.filter(id__in=other_top_items.top_track[:5])
                if other_top_items and other_top_items.top_track
                else None,
                "top_artists": Artist.objects.filter(
                    id__in=other_top_items.top_artist[:5]
                )
                if other_top_items and other_top_items.top_artist
                else None,
                "top_genres": other_top_items.top_genre[:5]
                if other_top_items
                else None,
                "iteratorRecentTracks": range(
                    min(5, len(other_recent_vibe.recent_track))
                )
                if other_recent_vibe
                else [],
                "iteratorTopTracks": range(min(5, len(other_top_items.top_track)))
                if other_top_items
                else [],
                "iteratorTopArtists": range(min(5, len(other_top_items.top_artist)))
                if other_top_items
                else [],
            },
        }

        # FRIEND REQUEST STATUSES -----
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
        # FRIEND REQUEST STATUSES END -----

        context = {
            "username": username,
            "user": user,
            "other_user": other_user,
            "info": info,
            "status": status,
        }

        return render(request, "view_profile/index.html", context)
    else:
        # No token, redirect to login again
        messages.error(request, "View_profile failed, please log in.")
        return redirect("login:index")


def generate_room_id(user_ids):
    sorted_user_ids = sorted(user_ids)
    room_id_hash = hash(tuple(sorted_user_ids))
    positive_hash = abs(room_id_hash)
    return (
        f"group_{positive_hash}"
        + str(timezone.now().hour)
        + str(timezone.now().minute)
        + str(timezone.now().second)
    )


def make_private_chatroom(user_id, other_user_id):
    room = (
        RoomModel.objects.filter(room_participants=user_id, room_type="direct_message")
        .filter(room_participants=other_user_id)
        .first()
    )
    if room is None:
        room_ID = generate_room_id([user_id, other_user_id])
        room_name = f"{other_user_id}"
        room = RoomModel.objects.create(
            roomID=room_ID,
            room_name=room_name,
            room_type="direct_message",
        )
        room.room_participants.add(user_id, other_user_id)
        room.save()


def process_fr(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id", None)
        other_user_id = request.POST.get("other_user_id", None)
        action = request.POST.get("action", None)
        where_from = request.POST.get("where_from", None)

        if (
            user_id is not None
            and other_user_id is not None
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
                    make_private_chatroom(user_id, other_user_id)
                    return redirect("chatroom:open_chatroom")

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
                return redirect("view_profile:compare", other_user_id=other_user_id)

    messages.error(request, "Process_fr form failed, please try again later.")
    return redirect("dashboard:index")
