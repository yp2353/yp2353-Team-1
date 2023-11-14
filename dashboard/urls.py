from django.urls import path

from . import views

app_name = "dashboard"
urlpatterns = [
    path("", views.index, name="index"),
    path("logout", views.logout, name="logout"),
    path(
        "get_task_status/<str:user_id>/<str:midnight>/",
        views.get_task_status,
        name="get_task_status",
    ),
]
