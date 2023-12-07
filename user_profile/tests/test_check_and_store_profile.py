from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.http import HttpRequest
from user_profile.views import check_and_store_profile
from user_profile.models import User
import datetime


class UserProfileTests(TestCase):
    def setUp(self):
        # Setup any initial data or state here
        self.request = HttpRequest()
        self.user = User(
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
        self.request.user = self.user

    @patch("user_profile.views.get_spotify_token")
    @patch("spotipy.Spotify")
    @patch("user_profile.models.User")
    def test_check_and_store_profile_new_user(
        self, mock_user_model, mock_spotify, mock_get_spotify_token
    ):
        # Simulate the scenario where a new user's data is fetched and stored

        # Setup mock for Spotify token
        mock_get_spotify_token.return_value = {"access_token": "test_token"}

        # Setup mock for Spotify API response
        user_info = {
            "id": "test_id",
            "display_name": "Test User",
            "followers": {"total": 100},
            "images": [{"url": "http://example.com/image.jpg"}],
            "country": "Test Country",
        }

        mock_track_info = {
            "album": {
                # ... [album details as per your format]
            },
            "artists": [
                # ... [artist details]
            ],
            "available_markets": [
                # ... [list of markets]
            ],
            "disc_number": 1,
            "duration_ms": 237546,
            "explicit": False,
            "external_ids": {"isrc": "USRC11600876"},
            "external_urls": {
                "spotify": "https://open.spotify.com/track/1WkMMavIMc4JZ8cfMmxHkI"
            },
            "href": "https://api.spotify.com/v1/tracks/1WkMMavIMc4JZ8cfMmxHkI",
            "id": "1WkMMavIMc4JZ8cfMmxHkI",
            "is_local": False,
            "name": "CAN'T STOP THE FEELING! (from DreamWorks Animation's \"TROLLS\")",
            "popularity": 75,
            "preview_url": "https://p.scdn.co/mp3-preview/8f4eee79e9574c8db62ebbdbbb5f14d6f9ed5fba?cid=a70c7a9100bd4330afa05deda868cf86",
            "track_number": 2,
            "type": "track",
            "uri": "spotify:track:1WkMMavIMc4JZ8cfMmxHkI",
        }

        mock_spotify.return_value.current_user.return_value = user_info
        mock_spotify.return_value.track.return_value = mock_track_info

        # Mock the User model
        mock_user_instance = MagicMock()
        mock_user_model.objects.filter.return_value.first.return_value = None
        mock_user_model.return_value = mock_user_instance

        # Call the function
        response = check_and_store_profile(self.request)

        # Assertions
        self.assertEqual(response.status_code, 200)

    # @patch("user_profile.views.get_spotify_token")
    # def test_check_and_store_profile_no_token(self, mock_get_spotify_token):
    #     # Test the behavior when there is no Spotify token

    #     # Setup mock for Spotify token to return None
    #     mock_get_spotify_token.return_value = None

    #     # Call the function
    #     response = check_and_store_profile(self.request)

    #     # Assertions
    #     self.assertEqual(response.status_code, 302)  # Redirect status code
    #     self.assertTrue(response["Location"].endswith("/login/"))

    # More tests can be added for different scenarios like updating an existing user, handling errors, etc.
