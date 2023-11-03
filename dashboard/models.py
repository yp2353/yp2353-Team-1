from django.db import models


# Create your models here.
class Track(models.Model):
    track_id = models.CharField(max_length=250, primary_key=True)
    track_name = models.CharField(max_length=250)
    track_cover_url = models.TextField(null=True)
    artist_name = models.CharField(max_length=250)
    artist_id = models.CharField(max_length=255)
    album_name = models.CharField(max_length=250)
    album_id = models.CharField(max_length=250)
    track_lyrics_vibe = models.CharField(max_length=250, null=True)
    track_audio_vibe = models.CharField(max_length=250, null=True)
    upvote_count = models.IntegerField(default=0)
    downvote_count = models.IntegerField(default=0)
    track_spotify_popularity = models.IntegerField(default=0)
    track_acousticness = models.DecimalField(null=True, max_digits=10, decimal_places=6)
    track_danceability = models.DecimalField(null=True, max_digits=10, decimal_places=6)
    track_energy = models.DecimalField(null=True, max_digits=10, decimal_places=6)
    track_loudness = models.DecimalField(null=True, max_digits=10, decimal_places=6)
    track_instrumentalness = models.DecimalField(
        null=True, max_digits=10, decimal_places=6
    )
    track_speechiness = models.DecimalField(null=True, max_digits=10, decimal_places=6)
    track_valence = models.DecimalField(null=True, max_digits=10, decimal_places=6)
