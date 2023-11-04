from django.urls import path

from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.index, name="index"),
    path("logout", views.logout, name="logout"),
    path("calculate_vibe", views.calculate_vibe, name="calculate_vibe"),
]
