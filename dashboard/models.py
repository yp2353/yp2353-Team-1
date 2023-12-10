from django.db import models
from django.contrib.postgres.fields import ArrayField


class TrackVibe(models.Model):
    track_id = models.CharField(max_length=250, primary_key=True)
    track_lyrics_vibe = models.CharField(max_length=250, null=True)
    track_audio_vibe = models.CharField(max_length=250, null=True)
    upvote_count = models.IntegerField(default=0)
    downvote_count = models.IntegerField(default=0)


class EmotionVector(models.Model):
    emotion = models.CharField(max_length=250, primary_key=True)
    vector = models.TextField()


class Track(models.Model):
    id = models.CharField(max_length=250, primary_key=True)
    name = models.TextField(null=True)
    popularity = models.IntegerField(default=0)
    album_name = models.TextField(null=True)
    album_release_date = models.TextField(null=True)
    album_images_large = models.TextField(null=True)
    album_images_small = models.TextField(null=True)
    artist_names = ArrayField(models.CharField(max_length=250), size=20, null=True)
    artist_ids = ArrayField(models.CharField(max_length=250), size=20, null=True)
    acousticness = models.FloatField(default=0.0)
    danceability = models.FloatField(default=0.0)
    energy = models.FloatField(default=0.0)
    instrumentalness = models.FloatField(default=0.0)
    loudness = models.FloatField(default=0.0)
    speechiness = models.FloatField(default=0.0)
    valence = models.FloatField(default=0.0)


class Artist(models.Model):
    id = models.CharField(max_length=250, primary_key=True)
    followers = models.IntegerField(default=0)
    genres = ArrayField(models.CharField(max_length=250), size=20, null=True)
    image = models.TextField(null=True)
    name = models.TextField(null=True)
    popularity = models.IntegerField(default=0)
