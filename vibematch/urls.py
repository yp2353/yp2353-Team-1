from django.urls import path

from . import views

app_name = "vibematch"

urlpatterns = [
    path("", views.vibe_match, name="vibe_match"),
]
