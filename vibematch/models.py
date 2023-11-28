from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

class UserLocation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,  # Use the custom user model
        on_delete=models.CASCADE
    )
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    created_at = models.DateTimeField(auto_now_add=True)
