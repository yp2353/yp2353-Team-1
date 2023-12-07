from django.test import TestCase
from unittest.mock import patch
from dashboard.models import TrackVibe
from dashboard.views import (
    get_recent_tracks,
)  # Assuming the function is in utils.py under dashboard app

# Mock data for Spotify API responses
mock_audio_features = [
    {
        "acousticness": 0.5,
        "danceability": 0.6,
        "energy": 0.7,
        "instrumentalness": 0.1,
        "valence": 0.3,
        "loudness": -10,
    }
]

mock_track_info = {
    "name": "Test Track",
    "id": "test_track_id",
    "album": {
        "release_date": "2023-01-01",
        "name": "Test Album",
        "images": [
            {"url": "large_image_url"},
            {"url": "medium_image_url"},
            {"url": "small_image_url"},
        ],
    },
    "artists": [{"name": "Test Artist"}],
    "uri": "test_uri",
}


class GetRecentTracksTests(TestCase):
    def setUp(self):
        TrackVibe.objects.create(
            track_id="test_track_id",
            track_lyrics_vibe="Happy",
            track_audio_vibe="Energetic",
        )

    @patch("spotipy.Spotify")
    def test_get_recent_tracks(self, MockSpotify):
        # Setup mock Spotipy client
        mock_sp = MockSpotify()
        mock_sp.audio_features.return_value = mock_audio_features
        mock_sp.track.return_value = mock_track_info

        track_ids = ["test_track_id"]
        final_tracks = get_recent_tracks(mock_sp, track_ids)

        self.assertEqual(len(final_tracks), 1)
        track = final_tracks[0]
        self.assertEqual(track["name"], "Test Track")
        self.assertEqual(track["id"], "test_track_id")
        self.assertEqual(track["year"], "2023")
        self.assertEqual(track["artists"], "Test Artist")
        self.assertEqual(track["album"], "Test Album")
        self.assertEqual(track["uri"], "test_uri")
        self.assertEqual(track["audio_vibe"], "Energetic")
        self.assertEqual(track["lyrics_vibe"], "Happy")

        # Assert the mock methods were called as expected
        mock_sp.audio_features.assert_called_once_with(["test_track_id"])
        mock_sp.track.assert_called_once_with("test_track_id")
