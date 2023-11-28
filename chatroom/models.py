from django.db import models

class ChatMessage(models.Model):
    content = models.TextField()
    sender = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)

