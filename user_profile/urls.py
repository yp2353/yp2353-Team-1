from django.urls import path

from . import views

app_name = "user_profile"
urlpatterns = [
    path("", views.check_and_store_profile, name="profile_page"),
    path("update/<str:user_id>", views.update_user_profile, name="update_profile"),
    path("processupdate/<str:user_id>", views.update, name="update"),
]
