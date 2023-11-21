# views.py
from django.shortcuts import render, HttpResponse, redirect
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from pusher import Pusher
from .models import ChatMessage
import os
from utils import get_spotify_token
import spotipy


pusher = Pusher(
    app_id=os.getenv("PUSHER_APP_ID"),
    key=os.getenv("PUSHER_KEY"),
    secret=os.getenv("PUSHER_SECRET"),
    cluster=os.getenv("PUSHER_CLUSTER"),
    ssl=True,
)


def chat(request):
    token_info = get_spotify_token(request)
    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        username = user_info["display_name"]
        messages = ChatMessage.objects.all()
        return render(
            request,
            "chats/globalchat.html",
            {"messages": messages, "username": username},
        )
    else:
        return redirect("login:index")


@csrf_exempt
def send_message(request):
    token_info = get_spotify_token(request)
    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        username = user_info["display_name"]
        if request.method == "POST":
            content = request.POST.get("content", "")

            if content and username:
                message = ChatMessage.objects.create(content=content, sender=username)
                pusher.trigger(
                    "chatroom",
                    "new_message",
                    {"message": message.content, "sender": message.sender},
                )
                return HttpResponse(status=201)

        return HttpResponse(status=400)
    else:
        return redirect("login:index")


def get_messages(request):
    if request.method == "GET":
        messages = ChatMessage.objects.all()
        message_list = [
            {"content": msg.content, "sender": msg.sender, "timestamp": msg.timestamp}
            for msg in messages
        ]
        return JsonResponse(message_list, safe=False)

    return HttpResponse(status=400)
