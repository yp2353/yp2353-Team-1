from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import patch
from user_profile.models import User
from view_profile.views import compare
import datetime


# Mock data and functions
mock_user_info = {"id": "user1_id", "display_name": "user1"}
mock_spotify_data = {
    "track": {},
    "tracks": {},
    "artists": {},
}  # Mock responses for Spotify API calls


def mock_get_spotify_token(*args, **kwargs):
    return {"access_token": "test_token"}


class CompareTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user1 = User.objects.create_user(
            username="testuser1",
            password="12345",
            user_id="test_user_id1",
            total_followers=100,
            profile_image_url="http://example.com/image.jpg",
            user_country="Test Country",
            user_last_login=datetime.datetime.now(),
            user_bio="Test Bio",
            user_city="Test City",
            user_total_friends=50,
            track_id="track123",
            # other fields as required
        )
        self.user1.save()

        self.user2 = User.objects.create_user(
            username="testuser2",
            password="12345",
            user_id="test_user_id2",
            total_followers=100,
            profile_image_url="http://example.com/image.jpg",
            user_country="Test Country",
            user_last_login=datetime.datetime.now(),
            user_bio="Test Bio",
            user_city="Test City",
            user_total_friends=50,
            track_id="track123",
            # other fields as required
        )
        self.user2.save()

    def _add_messages_storage_to_request(self, request):
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    @patch("spotipy.Spotify")
    def test_compare_success(self, MockSpotify):
        # Create a mock response that matches the structure returned by sp.current_user()
        mock_user_info = {"id": self.user1.user_id, "display_name": self.user1.username}

        # Setup the mock Spotify client
        mock_sp = MockSpotify()
        mock_sp.current_user.return_value = mock_user_info
        # Mock additional Spotify API calls as necessary

        # Using Django's test client for better handling of middleware
        self.client.force_login(self.user1)  # Assuming you have a self.user1 set up
        response = self.client.get(
            reverse("view_profile:compare", args=[self.user2.user_id])
        )

        # Test the response
        self.assertEqual(response.status_code, 200)

    @patch("spotipy.Spotify")
    def test_compare_one_user_not_exists(self, MockSpotify):
        mock_sp = MockSpotify()
        mock_sp.current_user.return_value = mock_user_info
        mock_sp.track.return_value = mock_spotify_data["track"]
        mock_sp.tracks.return_value = mock_spotify_data["tracks"]
        mock_sp.artists.return_value = mock_spotify_data["artists"]

        request = self.factory.get(
            reverse("view_profile:compare", args=["test_user_id2"])
        )

        request = self._add_messages_storage_to_request(request)
        request.user = self.user1
        self.client.force_login(self.user1)  # Assuming you have a self.user1 set up
        response = compare(request, self.user2.user_id)

        self.assertEqual(response.status_code, 200)
