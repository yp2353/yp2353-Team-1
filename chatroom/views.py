from rich.console import Console
from django.shortcuts import render

console = Console(style="bold green")


def open_chatroom(request):
    return render(request, "chatroom/chatroom.html")
