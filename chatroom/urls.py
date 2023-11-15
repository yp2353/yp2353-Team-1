from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

app_name = "chatroom"

urlpatterns = [
    path("", views.open_chatroom, name="open_chatroom"),
    path("api/chatroom/", views.chatroom_api, name="chatroom_api"),
    path('api/latest_messages/<str:room_id>/', views.get_latest_messages, name='get_latest_messages'),   
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
