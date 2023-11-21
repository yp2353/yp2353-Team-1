from django.test import TestCase
from unittest.mock import patch, MagicMock
from django.http import HttpRequest
from user_profile.views import check_and_store_profile


class UserProfileTests(TestCase):
    def setUp(self):
        # Setup any initial data or state here
        self.request = HttpRequest()

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
        mock_spotify.return_value.current_user.return_value = user_info

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
