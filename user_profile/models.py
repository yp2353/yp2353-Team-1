from django.db import models


# Create your models here.
class User(models.Model):
    user_id = models.CharField(max_length=250)
    username = models.CharField(max_length=125)
    total_followers = models.IntegerField()
    profile_image_url = models.URLField(null=True)
    user_country = models.CharField(max_length=200, null=True)
    user_last_login = models.DateTimeField()


#storing User vibe
class Vibe(models.Model):
    user_id = models.CharField(max_length=250)
    user_vibe = models.CharField(max_length=100)
    vibe_time = models.DateTimeField()

