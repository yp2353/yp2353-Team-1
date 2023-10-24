from django.db import models


# Create your models here.
class User(models.Model):
    user_id = models.CharField(max_length=250)
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
    user_vibe = models.CharField(max_length=100)
    vibe_time = models.DateTimeField()
