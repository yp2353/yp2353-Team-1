from django.db import models
from django.contrib.postgres.fields import ArrayField
from django.utils import timezone


# Create your models here.
class User(models.Model):
    user_id = models.CharField(max_length=250, primary_key=True)
    username = models.CharField(max_length=125)
    total_followers = models.IntegerField()
    profile_image_url = models.TextField(null=True)
    user_country = models.CharField(max_length=200, null=True)
    user_last_login = models.DateTimeField()
    user_bio = models.TextField(null=True)
    user_city = models.CharField(max_length=255, null=True)
    user_total_friends = models.IntegerField(null=True)

    def __str__(self) -> str:
        return f"User -> {self.user_id} ->  {self.username}"


# storing User vibe
class Vibe(models.Model):
    user_id = models.CharField(max_length=250)
    user_lyrics_vibe = models.CharField(max_length=250, null=True)
    user_audio_vibe = models.CharField(max_length=250, null=True)
    user_acousticness = models.DecimalField(null=True, max_digits=10, decimal_places=6)
    user_danceability = models.DecimalField(null=True, max_digits=10, decimal_places=6)
    user_energy = models.DecimalField(null=True, max_digits=10, decimal_places=6)
    user_valence = models.DecimalField(null=True, max_digits=10, decimal_places=6)
    recent_track = ArrayField(
        models.CharField(max_length=250),
        size=20,
        null=True
        )
    vibe_time = models.DateTimeField()


# storing User top items
class UserTop(models.Model):
    user_id = models.CharField(max_length=250)
    time = models.DateTimeField()
    recommended_tracks = ArrayField(
        models.CharField(max_length=250),
        size=20,
        null=True
        )
    top_track = ArrayField(
        models.CharField(max_length=250),
        size=20,
        null=True
        )
    top_artist = ArrayField(
        models.CharField(max_length=250),
        size=20,
        null=True
        )
    top_genre = ArrayField(
        models.CharField(max_length=250),
        size=20,
        null=True
        )

# User Friend List
class UserFriendRelation(models.Model):
    user1_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sender_user"
    )
    user2_id = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="receiver_user"
    )
    status = models.CharField(max_length=30, default="pending")
    status_update_time = models.DateField(default=timezone.now, editable=False)

    def __str__(self) -> str:
        return f"User -> {self.user1_id} ->  {self.user2_id} -> status"


# User Friend List
class FriendRequest(models.Model):
    sender = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="sent_request"
    )
    receiver = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="receive_request"
    )
    status = models.CharField(max_length=30, default="declined")
    request_time = models.DateField(default=timezone.now, editable=False)

