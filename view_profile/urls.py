from django.urls import path

from . import views

app_name = "view_profile"
urlpatterns = [
    path("compare/<str:other_user_id>/", views.compare, name="compare"),
    path("process_fr/", views.process_fr, name="process_fr"),
]
