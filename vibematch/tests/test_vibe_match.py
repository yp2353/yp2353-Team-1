import os
import pandas as pd
from django.conf import settings
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import patch
from dashboard.models import EmotionVector
from user_profile.models import Vibe, User
from vibematch.views import vibe_match
import json

# Mock data and functions
mock_user_info = {"id": "31riwbvwvrsgadgrerv6llzlmbpi", "display_name": "boyan"}
mock_spotify_data = {
    "track": {},
    "tracks": {},
    "artists": {},
}  # Mock responses for Spotify API calls


def mock_get_spotify_token(*args, **kwargs):
    return {"access_token": "test_token"}


class VibeMatchTests(TestCase):
    def setUp(self):
        # Assuming 'assets_path' is defined and points to the directory containing the CSV files
        assets_path = os.path.join(settings.BASE_DIR, "assets")

        # Constructing file paths
        emotionvector_file_path = os.path.join(
            assets_path, "test_dashboard_emotionvector_rows.csv"
        )
        vibe_file_path = os.path.join(assets_path, "test_user_profile_vibe_rows.csv")
        user_file_path = os.path.join(assets_path, "test_user_profile_user_rows.csv")

        # Loading the data from CSV files into pandas dataframes
        emotionvector_df = pd.read_csv(emotionvector_file_path)
        vibe_df = pd.read_csv(vibe_file_path)
        user_df = pd.read_csv(user_file_path)

        # Displaying the first few rows of each dataframe for inspection
        emotionvector_df.head(), vibe_df.head()

        self.factory = RequestFactory()
        # Load EmotionVector data
        for _, row in emotionvector_df.iterrows():
            EmotionVector.objects.create(emotion=row["emotion"], vector=row["vector"])

        # Load Vibe data
        for _, row in vibe_df.iterrows():
            Vibe.objects.create(
                user_id=row["user_id"],
                user_lyrics_vibe=row["user_lyrics_vibe"],
                user_audio_vibe=row["user_audio_vibe"],
                user_acousticness=row["user_acousticness"],
                user_danceability=row["user_danceability"],
                user_energy=row["user_energy"],
                user_valence=row["user_valence"],
                recent_track=json.loads(row["recent_track"].replace("'", '"')),
                vibe_time=pd.to_datetime(row["vibe_time"]),
                description=row["description"],
            )

        # Load User data
        for _, row in user_df.iterrows():
            if not User.objects.filter(username=row["username"]).exists():
                User.objects.create(
                    username=row["username"],
                    user_id=row["user_id"],
                    total_followers=row["total_followers"],
                    profile_image_url=row["profile_image_url"],
                    user_country=row["user_country"],
                    user_last_login=row["user_last_login"],
                    user_bio=row["user_bio"],
                    user_city=row["user_city"],
                    user_total_friends=0,
                    track_id=row["track_id"],
                )

    def _add_messages_storage_to_request(self, request):
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    @patch("spotipy.Spotify")
    def test_vibe_match_success(self, MockSpotify):
        mock_sp = MockSpotify()
        mock_sp.current_user.return_value = mock_user_info
        mock_sp.track.side_effect = lambda track_id: {"id": track_id}  # Mock track data
        mock_sp.artists.side_effect = lambda artist_ids: {
            "ids": artist_ids
        }  # Mock artist data

        request = self.factory.get(reverse("vibematch:vibe_match"))
        request = self._add_messages_storage_to_request(request)
        request.user = User.objects.get(user_id="31riwbvwvrsgadgrerv6llzlmbpi")
        response = vibe_match(request)

        self.assertEqual(response.status_code, 200)
        # Assertions to check the response content
        # e.g., self.assertIn("neighbors", response.context)
