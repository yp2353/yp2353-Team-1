from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from user_profile.models import Vibe
from django.utils import timezone


class VibeMatchTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Set up your Vibe test data here
        Vibe.objects.create(
            user_id="user1",
            user_lyrics_vibe="lyrics1",
            user_audio_vibe="audio1",
            user_acousticness=0.5,
            user_danceability=0.5,
            user_energy=0.5,
            user_valence=0.5,
            recent_track=["track1", "track2"],
            description="A description",
            vibe_time=timezone.now(),
        )

    @patch("vibematch.views.get_spotify_token")
    @patch("vibematch.views.spotipy.Spotify")
    def test_vibe_match_with_token(self, mock_spotify, mock_get_token):
        # Mock the Spotify token
        mock_get_token.return_value = {"access_token": "fake_token"}

        # Mock the Spotify client and its methods
        mock_spotify_instance = MagicMock()
        mock_spotify.return_value = mock_spotify_instance
        mock_spotify_instance.current_user.return_value = {"id": "user1"}

        # Call your view
        response = self.client.get(reverse("vibematch:vibe_match"))

        # Check response status and content
        self.assertEqual(response.status_code, 200)
        # Add more assertions to verify the response content

    @patch("vibematch.views.get_spotify_token")
    def test_vibe_match_without_token(self, mock_get_token):
        # Mock no Spotify token
        mock_get_token.return_value = None

        # Call your view
        response = self.client.get(reverse("vibematch:vibe_match"))

        # Check redirection to login
        self.assertRedirects(response, reverse("login:index"))

    # Additional tests can be written for the k_nearest_neighbors function
    # and its behavior under various scenarios (like no matches, one match, etc.)
