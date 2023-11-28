from django.db import models
from user_profile.models import User


class RoomModel(models.Model):
    roomID = models.TextField(primary_key=True)
    room_name = models.TextField()
    room_description = models.TextField()
    room_type = models.CharField(max_length=30)  # Direct Message or Group Chat
    room_participants = models.ManyToManyField(User, blank=True)

    def __str__(self):
        return self.room_name

    class Meta:
        verbose_name_plural = "Rooms"


class ChatMessage(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    room = models.ForeignKey(RoomModel, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
