# views.py
from rich.console import Console
from django.shortcuts import render, redirect
from utils import get_spotify_token
import spotipy
from user_profile.models import User
from .models import RoomModel
from .forms import SearchRoomFrom


console = Console(style="bold green")

user_exists = None


def open_chatroom(request):
    global user_exists
    token_info = get_spotify_token(request)

    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        user_id = user_info["id"]

        user_exists = User.objects.filter(user_id=user_id).first()
        rooms_list = RoomModel.objects.filter(room_participants=user_id)

        if not rooms_list:
            room = RoomModel.objects.get(roomID="global_room")
            room.room_participants.add(user_exists)
            print("=====New User Added to global room +++++")

        form = SearchRoomFrom()
        print(rooms_list)

        context = {
            "user": user_exists,
            "rooms_list": rooms_list,
            "SearchRoomFrom": form,
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


def get_user_exist():
    global user_exists
    if user_exists:
        # print("Got user", user_exists)
        return user_exists
    else:
        print("No get_user_exist")
