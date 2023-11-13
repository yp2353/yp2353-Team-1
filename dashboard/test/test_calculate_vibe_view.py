import json
from django.test import TestCase, RequestFactory
from django.urls import reverse
from unittest.mock import patch
from django.contrib.sessions.middleware import SessionMiddleware
from dashboard.views import calculate_vibe  # Adjust the import path as necessary


class CalculateVibeViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def add_session_to_request(self, request):
        """Add a session to the request object."""
        middleware = SessionMiddleware(lambda _: _)
        middleware.process_request(request)
        request.session.save()

    @patch("dashboard.views.get_spotify_token")  # Mock the get_spotify_token function
    @patch("spotipy.Spotify")  # Mock the Spotify client
    def test_calculate_vibe_with_token_and_no_recent_vibe(
        self, mock_spotify, mock_get_token
    ):
        # Setup mock Spotify API responses
        mock_sp = mock_spotify.return_value
        mock_sp.current_user.return_value = {"id": "testuserid"}
        mock_sp.current_user_recently_played.return_value = {
            "items": []
        }  # Mock recent tracks

        # Mock token info
        mock_get_token.return_value = {"access_token": "testtoken"}

        # Create a request object
        request = self.factory.get(reverse("dashboard:calculate_vibe"))

        # Call the view
        response = calculate_vibe(request)

        # Parse the JSON content
        response_data = json.loads(response.content)

        # Check the response content
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response_data, {"result": "Null", "description": "No description available"}
        )  # Expected JSON response

    @patch("dashboard.views.get_spotify_token")
    @patch("spotipy.Spotify")
    def test_calculate_vibe_without_token(self, mock_spotify, mock_get_token):
        # Setup mock to return None (no token)
        mock_get_token.return_value = None

        # Create a request object
        request = self.factory.get(reverse("dashboard:calculate_vibe"))

        # Manually add a session to the request
        self.add_session_to_request(request)

        # Call the view
        response = calculate_vibe(request)

        # Assert the response for redirection or other expected behavior
        self.assertEqual(response.status_code, 302)  # or other assertions
