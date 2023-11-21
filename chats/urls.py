# chat/urls.py
from django.urls import path
from .views import chat, send_message, get_messages

app_name = "chats"
urlpatterns = [
    path("chat/", chat, name="chat"),
    path("send_message/", send_message, name="send_message"),
    path("get_messages/", get_messages, name="get_messages"),
]
