from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from search.views import open_search_page


class OpenSearchPageTest(TestCase):
    def setUp(self):
        self.client = Client()

        # Mock Spotify API responses
        self.mock_spotify_user = {
            "id": "test_spotify_user_id",
            "display_name": "Test User",
        }

    @patch("search.views.get_spotify_token")
    @patch("spotipy.Spotify.current_user")
    def test_open_search_page_with_valid_token(self, mock_current_user, mock_get_token):
        # Set up mock responses
        mock_get_token.return_value = {"access_token": "testtoken"}
        mock_current_user.return_value = self.mock_spotify_user

        # Create an authenticated request
        request = self.client.get(reverse("search:search_page"))

        # Call the view
        response = open_search_page(request)

        # Check response status code and template used
        self.assertEqual(response.status_code, 200)

        # Check context data
        # ... check other context data ...

    @patch("search.views.get_spotify_token")
    def test_open_search_page_without_token(self, mock_get_token):
        # Set up mock response
        mock_get_token.return_value = None

        # Create an unauthenticated request
        response = self.client.get(reverse("search:search_page"))

        # Check redirect
        self.assertRedirects(
            response, reverse("login:index"), status_code=302, target_status_code=200
        )

    # ... Additional tests for other scenarios and context data ...
