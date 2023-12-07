from django.test import TestCase
from django.urls import reverse
from dashboard.models import TrackVibe
import json


class DashboardViewTests(TestCase):
    def setUp(self):
        # Create a TrackVibe instance for testing
        self.track = TrackVibe.objects.create(
            track_id="test_track_id",
            track_lyrics_vibe="Happy",
            track_audio_vibe="Energetic",
        )

    def test_upvote_track(self):
        response = self.client.post(
            reverse("dashboard:upvote_track", args=[self.track.track_id])
        )
        self.assertEqual(response.status_code, 200)
        self.track.refresh_from_db()
        self.assertEqual(self.track.upvote_count, 1)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["upvote_count"], 1)

    def test_cancel_upvote_track(self):
        # Manually set upvote count for testing
        self.track.upvote_count = 1
        self.track.save()

        response = self.client.post(
            reverse("dashboard:cancel_upvote_track", args=[self.track.track_id])
        )
        self.assertEqual(response.status_code, 200)
        self.track.refresh_from_db()
        self.assertEqual(self.track.upvote_count, 0)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["upvote_count"], 0)

    def test_downvote_track(self):
        response = self.client.post(
            reverse("dashboard:downvote_track", args=[self.track.track_id])
        )
        self.assertEqual(response.status_code, 200)
        self.track.refresh_from_db()
        self.assertEqual(self.track.downvote_count, 1)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["downvote_count"], 1)

    def test_cancel_downvote_track(self):
        # Manually set downvote count for testing
        self.track.downvote_count = 1
        self.track.save()

        response = self.client.post(
            reverse("dashboard:cancel_downvote_track", args=[self.track.track_id])
        )
        self.assertEqual(response.status_code, 200)
        self.track.refresh_from_db()
        self.assertEqual(self.track.downvote_count, 0)
        response_data = json.loads(response.content)
        self.assertEqual(response_data["downvote_count"], 0)
