from django.urls import path

from . import views

app_name = "login"
urlpatterns = [
    path("", views.index, name="index"),
    path(
        "authenticate_spotify", views.authenticate_spotify, name="authenticate_spotify"
    ),
    path("callback", views.callback, name="callback"),
]
