from django.urls import path

from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.index, name="index"),
    path("logout", views.logout, name="logout"),
    path(
        "get_task_status/<str:midnight>/",
        views.get_task_status,
        name="get_task_status",
    ),
    path("track/<str:track_id>/upvote/", views.upvote_track, name="upvote_track"),
    path("track/<str:track_id>/downvote/", views.downvote_track, name="downvote_track"),
    path(
        "track/<str:track_id>/cancel_upvote/",
        views.cancel_upvote_track,
        name="cancel_upvote_track",
    ),
    path(
        "track/<str:track_id>/cancel_downvote/",
        views.cancel_downvote_track,
        name="cancel_downvote_track",
    ),
]
