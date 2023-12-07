from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.messages import get_messages
from user_profile.models import User
from user_profile.views import changeTrack
import datetime


class ChangeTrackViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            username="testuser",
            password="12345",
            user_id="123",
            total_followers=100,
            profile_image_url="http://example.com/image.jpg",
            user_country="Test Country",
            user_last_login=datetime.datetime.now(),
            user_bio="Test Bio",
            user_city="Test City",
            user_total_friends=50,
            track_id="track123",
        )

    def _add_messages_storage_to_request(self, request):
        """
        Add a message storage to the request to simulate the messages framework.
        """
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    def test_change_track_remove_existing_user(self):
        request = self.factory.post(
            reverse("user_profile:changeTrack"), {"user_id": "123", "action": "remove"}
        )
        request.user = self.user
        request = self._add_messages_storage_to_request(request)
        response = changeTrack(request)
        self.user.refresh_from_db()
        self.assertIsNone(self.user.track_id)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("user_profile:profile_page"))

    def test_change_track_add_existing_user(self):
        request = self.factory.post(
            reverse("user_profile:changeTrack"),
            {"user_id": "123", "action": "add", "track_id": "new_track_id"},
        )
        request.user = self.user
        request = self._add_messages_storage_to_request(request)
        response = changeTrack(request)
        self.user.refresh_from_db()
        self.assertEqual(self.user.track_id, "new_track_id")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("user_profile:profile_page"))

    def test_change_track_non_existing_user(self):
        request = self.factory.post(
            reverse("user_profile:changeTrack"),
            {"user_id": "non_existent_user", "action": "remove"},
        )
        request.user = self.user
        request = self._add_messages_storage_to_request(request)
        response = changeTrack(request)
        messages = list(get_messages(request))
        self.assertTrue(
            any(
                message.message
                == "Changing track failed, please try again later. User unavailable."
                for message in messages
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login:index"))

    def test_change_track_invalid_post_request(self):
        request = self.factory.post(reverse("user_profile:changeTrack"))
        request.user = self.user
        request = self._add_messages_storage_to_request(request)
        response = changeTrack(request)
        messages = list(get_messages(request))
        self.assertTrue(
            any(
                message.message == "Change track failed, please try again later."
                for message in messages
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:index"))
