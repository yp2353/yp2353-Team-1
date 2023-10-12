from django.urls import path

from . import views

app_name = 'login'
urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard", views.dashboard, name='dashboard'),
    path('authenticate_spotify', views.authenticate_spotify, name='authenticate_spotify'),
    path('callback', views.callback, name='callback'),
    path('logout_view', views.logout_view, name='logout_view'),
]