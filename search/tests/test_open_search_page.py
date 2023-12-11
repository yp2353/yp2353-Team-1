from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.messages.storage.fallback import FallbackStorage
from unittest.mock import patch
from search.forms import UsersearchForm  # Replace 'search' with the actual app name
from user_profile.models import User
import datetime

# Mock data and functions
mock_spotify_token = {"access_token": "test_token"}
mock_user_info = {"id": "test_user_id", "display_name": "test_username"}


class OpenSearchPageTests(TestCase):
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

    def _add_messages_storage_to_request(self, request):
        setattr(request, "session", "session")
        messages = FallbackStorage(request)
        setattr(request, "_messages", messages)
        return request

    # @patch("search.views.get_spotify_token", return_value=mock_spotify_token)
    @patch("spotipy.Spotify.current_user", return_value=mock_user_info)
    @patch("search.views.get_req_list", return_value=[])
    @patch("search.views.current_friend_list", return_value=[])
    def test_open_search_page_success(
        self,
        mock_friend_list,
        mock_req_list,
        mock_current_user,
    ):
        self.client.login(username="testuser1", password="12345")
        response = self.client.get(reverse("search:search_page"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("UsersearchForm", response.context)
        self.assertIsInstance(response.context["UsersearchForm"], UsersearchForm)
        self.assertEqual(response.context["username"], "testuser1")

    # @patch("search.views.get_spotify_token", return_value=None)
    # def test_open_search_page_no_token(self, mock_get_token):
    #     request = self.factory.get(reverse("search:search_page"))
    #     request = self._add_messages_storage_to_request(request)
    #     response = open_search_page(request)
    #     messages = list(get_messages(request))
    #     self.assertTrue(
    #         any(
    #             message.message == "Open_search_page failed, please try again later."
    #             for message in messages
    #         )
    #     )
    #     self.assertEqual(response.status_code, 302)
    #     self.assertEqual(response.url, reverse("login:index"))
