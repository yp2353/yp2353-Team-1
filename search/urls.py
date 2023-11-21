from django.urls import path

from . import views

app_name = "search"
urlpatterns = [
    path("", views.open_search_page, name="search_page"),
    path("search_user/", views.user_search, name="search_user"),
]
