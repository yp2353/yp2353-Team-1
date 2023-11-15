# views.py
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .models import RoomModel
from .forms import SearchRoomFrom
from .consumer import GlobalChatConsumer
from utils import get_spotify_token
from user_profile.models import User
import spotipy
from .models import ChatMessage


class ChatRoomView(View):
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, *args, **kwargs):
        return JsonResponse({"error": "Method not allowed"}, status=405)

    def post(self, request, *args, **kwargs):
        room_id = request.POST.get("roomID")
        if room_id:
            consumer = GlobalChatConsumer()
            response = consumer.post(request, roomID=room_id, type="join_room")
            messages = response.get("messages", [])
            return JsonResponse({"messages": messages})
        return JsonResponse({"error": "Invalid request"})


user_exists = None


def open_chatroom(request):
    global user_exists
    token_info = get_spotify_token(request)

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

        form = SearchRoomFrom()
        print(rooms_list)

        context = {
            "username": username,
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


# New view for handling chat room API requests
@csrf_exempt
def chatroom_api(request):
    if request.method == "POST":
        data = request.POST
        print("Received data:", data)  # Add print statements for debugging purposes
        message_type = data.get("type")

        if message_type == "join_room":
            room_id = data.get("roomID")

            # Retrieve previous messages from the database
            room_messages = ChatMessage.objects.filter(room=room_id)
            messages = []

            for message in room_messages:
                sender_username = message.sender.username
                messages.append(
                    {
                        "type": "chat_message",
                        "message": message.content,
                        "sender": sender_username,
                    }
                )

            return JsonResponse(
                {
                    "messages": messages,
                    "sender": get_user_exist().username,
                }
            )

        elif message_type == "chat_message":
            # Handle sending a chat message
            room_id = data.get("roomID")
            message = data.get("message")
            sender_username = get_user_exist().username
            save_message = ChatMessage.objects.create(
                sender=get_user_exist(),
                room=RoomModel.objects.get(roomID=room_id),
                content=message,
            )
            save_message.save()

            return JsonResponse(
                {"sender": sender_username, "message": message, "success": True}
            )

    return JsonResponse({"error": "Invalid request"})
