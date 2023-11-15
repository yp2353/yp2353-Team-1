from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = "chatroom"

urlpatterns = [
    path("", views.open_chatroom, name="open_chatroom"),
    path("api/chatroom/", views.chatroom_api, name="chatroom_api"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
