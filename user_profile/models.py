from django.db import models
from django.contrib.postgres.fields import ArrayField


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
    user_genre = models.CharField(max_length=250, null=True)

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
    recent_track = ArrayField(models.CharField(max_length=250), size=20)
    recommended_tracks = ArrayField(models.CharField(max_length=250), size=20)
    top_track = ArrayField(models.CharField(max_length=250), size=20)
    top_artist = ArrayField(models.CharField(max_length=250), size=20)
    top_genre = ArrayField(models.CharField(max_length=250), size=20)
    vibe_time = models.DateTimeField()
