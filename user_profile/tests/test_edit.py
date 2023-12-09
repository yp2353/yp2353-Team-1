from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from user_profile.models import User
from user_profile.views import edit
import datetime


class EditViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user_id = "test_user_id"
        self.user = User(
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

    def test_update_view_non_post_request(self):
        # Testing non-POST request
        request = self.factory.get(reverse("user_profile:edit"))
        request.user = self.user
        request = self._add_messages_storage_to_request(request)
        response = edit(request)
        messages = list(get_messages(request))
        self.assertTrue(
            any(
                message.message == "Edit profile failed, please try again later."
                for message in messages
            )
        )
        self.assertEqual(response.url, reverse("login:index"))
        self.assertEqual(response.status_code, 302)  # Redirect status code

    def test_update_view_post_request_non_existing_user(self):
        # Testing POST request for a non-existing user
        request = self.factory.post(
            reverse("user_profile:edit"), {"user_id": "non_existing_user_id"}
        )
        request.user = self.user
        request = self._add_messages_storage_to_request(request)
        response = edit(request)
        messages = list(get_messages(request))
        self.assertTrue(
            any(
                message.message
                == "Edit profile failed, please try again later. User unavailable."
                for message in messages
            )
        )
        self.assertEqual(response.url, reverse("login:index"))
        self.assertEqual(response.status_code, 302)  # Redirect status code
