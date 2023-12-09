from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages import get_messages
from django.contrib.messages.storage.fallback import FallbackStorage
from user_profile.models import User, UserFriendRelation
from view_profile.views import process_fr
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


class ProcessFrTests(TestCase):
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

        self.friend_request = UserFriendRelation.objects.create(
            user1_id=self.user1,
            user2_id=self.user2,
            status="pending",
            status_update_time=datetime.date.today(),
        )

    def _add_messages_storage_to_request(self, request):
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    def test_process_fr_send_request(self):
        post_data = {
            "user_id": self.user1.user_id,
            "other_user_id": self.user2.user_id,
            "action": "send",
            "where_from": "search_request_list",
        }
        request = self.factory.post(reverse("view_profile:process_fr"), post_data)
        request = self._add_messages_storage_to_request(request)
        response = process_fr(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("search:search_page"))

        # Check the status of the friend request
        friend_request = UserFriendRelation.objects.get(
            user1_id=self.user1, user2_id=self.user2
        )
        self.assertEqual(friend_request.status, "pending")

    # Add more tests for cancel, unfriend, accept, decline actions

    def test_process_fr_invalid_post(self):
        post_data = {
            "user_id": self.user1.user_id,
            # Missing other fields
        }
        request = self.factory.post(reverse("view_profile:process_fr"), post_data)
        request = self._add_messages_storage_to_request(request)
        response = process_fr(request)

        messages = list(get_messages(request))
        self.assertTrue(
            any(
                message.message == "Process_fr form failed, please try again later."
                for message in messages
            )
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:index"))

    def test_process_fr_accept_request(self):
        # Setup a pending friend request
        UserFriendRelation.objects.create(
            user1_id=self.user2,
            user2_id=self.user1,
            status="pending",
        )

        post_data = {
            "user_id": self.user1.user_id,
            "other_user_id": self.user2.user_id,
            "action": "accept",
            "where_from": "search_request_list",
        }

        request = self.factory.post(reverse("view_profile:process_fr"), post_data)
        request = self._add_messages_storage_to_request(request)
        response = process_fr(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("search:search_page"))

        friend_request = UserFriendRelation.objects.get(
            user1_id=self.user2, user2_id=self.user1
        )
        self.assertEqual(friend_request.status, "friends")

    def test_process_fr_decline_request(self):
        # Setup a pending friend request
        UserFriendRelation.objects.create(
            user1_id=self.user2,
            user2_id=self.user1,
            status="pending",
        )

        post_data = {
            "user_id": self.user1.user_id,
            "other_user_id": self.user2.user_id,
            "action": "decline",
            "where_from": "search_request_list",
        }

        request = self.factory.post(reverse("view_profile:process_fr"), post_data)
        request = self._add_messages_storage_to_request(request)
        response = process_fr(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("search:search_page"))

        friend_request = UserFriendRelation.objects.get(
            user1_id=self.user2, user2_id=self.user1
        )
        self.assertEqual(friend_request.status, "not_friend")

    def test_process_fr_request_not_exist_send(self):
        post_data = {
            "user_id": self.user1.user_id,
            "other_user_id": self.user2.user_id,
            "action": "send",
            "where_from": "search_request_list",
        }

        request = self.factory.post(reverse("view_profile:process_fr"), post_data)
        request = self._add_messages_storage_to_request(request)
        response = process_fr(request)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("search:search_page"))

        friend_request = UserFriendRelation.objects.get(
            user1_id=self.user1, user2_id=self.user2
        )
        self.assertEqual(friend_request.status, "pending")
