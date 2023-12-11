from django.test import TestCase
from dashboard.models import TrackVibe, Track
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
        ).save()

        Track.objects.create(
            id="test_track_id",
            name="Test Track",
            popularity=85,
            album_name="Test Album",
            album_release_date="2023-05-26",
            album_images_large="test_uri",
            album_images_small="test_uri",
            artist_names=["Test Artist"],
            artist_ids=["23456bcdef"],
            acousticness=0.3,
            danceability=0.5,
            energy=0.7,
            instrumentalness=0.01,
            loudness=-5.3,
            speechiness=0.03,
            valence=0.8,
        ).save()

    def test_get_recent_tracks(self):
        # Setup mock Spotipy client

        final_tracks = get_recent_tracks(["test_track_id"])
        self.assertEqual(len(final_tracks), 1)
        track = final_tracks[0]
        self.assertEqual(track["name"], "Test Track")
        self.assertEqual(track["id"], "test_track_id")
        self.assertEqual(track["year"], "2023")
        self.assertEqual(track["artists"], "Test Artist")
        self.assertEqual(track["album"], "Test Album")
        self.assertEqual(track["audio_vibe"], "Energetic")
        self.assertEqual(track["lyrics_vibe"], "Happy")
