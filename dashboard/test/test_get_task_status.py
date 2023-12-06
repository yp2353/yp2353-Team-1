from django.test import TestCase, RequestFactory
from django.urls import reverse
from unittest.mock import patch
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from user_profile.models import Vibe
from dashboard.views import (
    get_task_status,
)  # Replace 'your_app' with the actual app name
import datetime
import json

# Mock data and functions
mock_spotify_token = {"access_token": "test_token"}
mock_user_info = {"id": "test_user_id"}
mock_recent_tracks = [{"name": "Test Track", "id": "test_track_id"}]


class GetTaskStatusTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user_id = "test_user_id"
        self.midnight = datetime.datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        Vibe.objects.create(
            user_id=self.user_id,
            user_audio_vibe="Happy",
            user_lyrics_vibe="Energetic",
            description="Test Description",
            vibe_time=datetime.datetime.now(),
            recent_track=["test_track_id"],
        )

    def _add_messages_storage_to_request(self, request):
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    @patch("dashboard.views.get_spotify_token", return_value=mock_spotify_token)
    @patch("spotipy.Spotify.current_user", return_value=mock_user_info)
    @patch("dashboard.views.get_recent_tracks", return_value=mock_recent_tracks)
    def test_get_task_status_success(
        self, mock_get_recent_tracks, mock_current_user, mock_get_token
    ):
        midnight_str = self.midnight.strftime("%Y-%m-%dT%H:%M:%S")
        request = self.factory.get(
            reverse("dashboard:get_task_status", args=[midnight_str])
        )
        request = self._add_messages_storage_to_request(request)
        response = get_task_status(request, midnight_str)
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["status"], "SUCCESS")
        self.assertEqual(response_data["result"], "Happy Energetic")
        self.assertEqual(response_data["description"], "Test Description")
        self.assertEqual(response_data["recent_tracks"], mock_recent_tracks)

    @patch("dashboard.views.get_spotify_token", return_value=None)
    def test_get_task_status_no_token(self, mock_get_token):
        midnight_str = self.midnight.strftime("%Y-%m-%dT%H:%M:%S")
        request = self.factory.get(
            reverse("dashboard:get_task_status", args=[midnight_str])
        )
        request = self._add_messages_storage_to_request(request)
        response = get_task_status(request, midnight_str)
        messages = list(get_messages(request))
        self.assertTrue(
            any(
                message.message == "Get_task_status failed, please try again later."
                for message in messages
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login:index"))
