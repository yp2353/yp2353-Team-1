from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
from dashboard.views import index  # Adjust the import path as necessary


class IndexViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()

    @patch("dashboard.views.get_spotify_token")  # Mock the get_spotify_token function
    @patch("spotipy.Spotify")  # Mock the Spotify client
    def test_index_view_with_token(self, mock_spotify, mock_get_token):
        # Setup mock Spotify API responses
        mock_sp = mock_spotify.return_value
        mock_sp.current_user.return_value = {
            "display_name": "Test User",
            "id": "testuserid",
        }
        mock_sp.current_user_top_tracks.return_value = {
            "items": []
        }  # Mock top tracks data

        # Mock session data
        mock_get_token.return_value = {"access_token": "testtoken"}

        # Create a request object

        # Call the view
        response = self.client.get(reverse("dashboard:index"))

        # Check if the response is as expected
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "dashboard/index.html"
        )  # Check if correct template is used

    @patch("dashboard.views.get_spotify_token")
    def test_index_view_without_token(self, mock_get_token):
        # Mock session data to simulate no token
        mock_get_token.return_value = None

        # Create a request object
        request = self.client.get(reverse("dashboard:index"))  # Adjust the view name
        request.session = {}  # Set up a mock session

        # Call the view
        response = index(request)

        # Check if redirection happens
        self.assertEqual(
            response.status_code, 302
        )  # 302 is the status code for redirection
        self.assertTrue(
            response.url.startswith("/login/")
        )  # Check if it redirects to the login page
