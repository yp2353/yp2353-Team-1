from django.urls import path

from . import views

app_name = 'user_profile'
urlpatterns = [
    path("", views.check_and_store_profile, name="profile_page"),
]