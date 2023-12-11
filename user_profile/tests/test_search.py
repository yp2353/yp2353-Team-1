from django.test import TestCase, RequestFactory
from django.urls import reverse
from user_profile.models import User
from django.contrib.messages import get_messages
from unittest.mock import patch
from user_profile.forms import SearchForm
import datetime


# Mocking the Spotify API response
def mock_spotify_search(*args, **kwargs):
    return {
        "tracks": {
            "items": [
                {
                    "id": "track_id",
                    "name": "track_name",
                    "artists": [{"name": "artist_name"}],
                    "album": {
                        "name": "album_name",
                        "images": [{"url": "image_url"}],
                        "release_date": "release_date",
                    },
                }
            ]
        }
    }


def mock_spotify_track(*args, **kwargs):
    return {
        "id": "track_id",
        "name": "track_name",
        "artists": [{"name": "artist_name"}],
        "album": {
            "name": "album_name",
            "images": [{"url": "image_url"}],
            "release_date": "release_date",
        },
    }


def mock_get_spotify_token(*args, **kwargs):
    return {"access_token": "test_token"}


class SearchViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser",
            password="12345",
            user_id="123",
            total_followers=100,
            profile_image_url="http://example.com/image.jpg",
            user_country="Test Country",
            user_last_login=datetime.datetime.now(),
            user_bio="Test Bio",
            user_city="Test City",
            user_total_friends=50,
            track_id="track123",
        )
        self.user.set_password("12345")
        self.user.save()

    @patch("user_profile.views.get_spotify_token", side_effect=mock_get_spotify_token)
    @patch("spotipy.Spotify.search", side_effect=mock_spotify_search)
    @patch("spotipy.Spotify.track", side_effect=mock_spotify_track)
    def test_search_view_authenticated_user_valid_search(
        self, mock_track, mock_search, mock_token
    ):
        login_successful = self.client.login(username="testuser", password="12345")
        self.assertTrue(login_successful)
        response = self.client.get(
            reverse("user_profile:search"), {"search_query": "test_query"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.context)
        self.assertIsInstance(response.context["SearchForm"], SearchForm)
        self.assertTrue(mock_search.called)

    def test_search_view_unauthenticated_user(self):
        response = self.client.get(reverse("user_profile:search"))
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(
            any(
                message.message
                == "Profile track search failed, please try again later."
                for message in messages
            )
        )
        self.assertEqual(response.status_code, 302)  # Redirect status code
        self.assertEqual(response.url, reverse("login:index"))
