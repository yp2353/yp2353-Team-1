# chatroom/views.py
from rich.console import Console
from django.shortcuts import render, redirect
from django.http import HttpResponse
import spotipy


console = Console(style="bold green")

user_exists = None


def open_chatroom(request):
    from search.views import current_friend_list
    from user_profile.models import User
    from utils import get_spotify_token

    global user_exists
    token_info = get_spotify_token(request)
    from chatroom.models import RoomModel
    from .forms import SearchRoomFrom

    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        user_id = user_info["id"]
        username = user_info["display_name"]

        user_exists = User.objects.filter(user_id=user_id).first()
        rooms_list = RoomModel.objects.filter(room_participants=user_id)

        if not rooms_list:
            room = RoomModel.objects.get(roomID="global_room")
            room.room_participants.add(user_exists)
            print("=====New User Added to global room +++++")

        for room in rooms_list:
            if room.room_type == "direct_message":
                other_user = room.room_participants.exclude(user_id=user_id).first()
                print(other_user)
                room.room_name = other_user.username
                print(room.room_name)

        form = SearchRoomFrom()
        print(rooms_list)

        friends = current_friend_list(user_id)

        context = {
            "username": username,
            "user": user_exists,
            "rooms_list": rooms_list,
            "SearchRoomFrom": form,
            "friends": friends,
        }
        return render(request, "chatroom/chatroom.html", context)
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")


def get_room_details(roomID):
    return None


def search_room(request):
    return None


def get_user_exist(user_id):
    from user_profile.models import User

    if user_id:
        user_exists = User.objects.filter(user_id=user_id).first()
        return user_exists
    else:
        return None


def group_creation(request):
    from view_profile.views import generate_room_id, make_private_chatroom
    from utils import get_spotify_token
    from chatroom.models import RoomModel

    token_info = get_spotify_token(request)
    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        user_id = user_info["id"]

        if request.method == "POST":
            selected_friends = request.POST.getlist(
                "selected_friends"
            )  # 'selected_rooms' is the name attribute of the checkbox

            if len(selected_friends) == 0:
                return redirect("chatroom:open_chatroom")

            if len(selected_friends) == 1:
                make_private_chatroom(user_id, other_user_id=selected_friends[0])
                return redirect("chatroom:open_chatroom")

            selected_friends.append(user_id)
            print(selected_friends)

            room_ID = generate_room_id(
                selected_friends
            )  # This function would generate a unique ID for the group room
            group_room_count = RoomModel.objects.filter(room_type="group").count()
            room_name = f"Group{group_room_count + 1:03d}"
            room = RoomModel.objects.create(
                roomID=room_ID, room_name=room_name, room_type="group"
            )

            room.room_participants.set(
                selected_friends
            )  # This sets all the user IDs at once for the participants
            room.save()
            return redirect("chatroom:open_chatroom")

        else:
            return HttpResponse("Method not allowed", status=405)
    else:
        return redirect("login:index")


def update_room_name(request):
    from django.http import JsonResponse
    from chatroom.models import RoomModel

    if request.method == "POST":
        room_id = request.POST.get("room_id")
        new_name = request.POST.get("new_name")
        print(room_id)
        print(new_name)

        try:
            room = RoomModel.objects.get(roomID=room_id)
            room.room_name = new_name
            room.save()
            return JsonResponse({"success": True})
        except RoomModel.DoesNotExist:
            return JsonResponse({"success": False, "error": "Room does not exist."})
    return JsonResponse({"success": False, "error": "Invalid request"})
