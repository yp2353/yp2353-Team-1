from django.urls import path

from . import views

app_name = "view_profile"
urlpatterns = [
    path("other/<str:other_user_id>/", views.other, name="other"),
    path("process_fr/", views.process_fr, name="process_fr"),
]
