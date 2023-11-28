from django.db import models


class TrackVibe(models.Model):
    track_id = models.CharField(max_length=250, primary_key=True)
    track_lyrics_vibe = models.CharField(max_length=250, null=True)
    track_audio_vibe = models.CharField(max_length=250, null=True)
    upvote_count = models.IntegerField(default=0)
    downvote_count = models.IntegerField(default=0)


class EmotionVector(models.Model):
    emotion = models.CharField(max_length=250, primary_key=True)
    vector = models.TextField()
