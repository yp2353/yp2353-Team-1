from django.test import TestCase, RequestFactory
from django.urls import reverse
from unittest.mock import patch, MagicMock
from search.views import (
    process_friend_request,
)
from user_profile.models import User, UserFriendRelation
from test_utils import load_test_data


class ProcessFriendRequestTest(TestCase):
    def setUp(self):
        load_test_data()

        self.factory = RequestFactory()
        self.user_id = "31riwbvwvrsgadgrerv6llzlmbpi"  # Mock user ID
        self.friend_user_id = "l584nmd717fk2meevv14ng8ogw"  # Mock friend user ID

        # Mocking Spotify API response
        self.spotify_user_info = {"id": self.user_id, "display_name": "mock_name"}

        # Mocking the database models
        self.mock_user = MagicMock()
        self.mock_user_friend_relation = MagicMock()

    def test_cancel_action(self):
        self.friend_action("cancel")

    def test_unfriend_action(self):
        self.friend_action("unfriend")

    # def test_send_action(self):
    #     self.friend_action("send")

    def test_accept_action(self):
        self.friend_action("accept")

    def test_decline_action(self):
        self.friend_action("decline")

    def friend_action(self, action):
        with patch("search.views.get_spotify_token") as mock_get_spotify_token, patch(
            "search.views.spotipy.Spotify"
        ) as mock_spotify, patch("user_profile.models.User", new=self.mock_user), patch(
            "user_profile.models.UserFriendRelation", new=self.mock_user_friend_relation
        ), patch(
            "spotipy.Spotify.current_user"
        ) as mock_current_user:
            # Setup mock for Spotify token
            mock_get_spotify_token.return_value = {"access_token": "mock_token"}
            mock_current_user.return_value = self.spotify_user_info

            # Setup mock for Spotify API response
            mock_spotify_instance = mock_spotify.return_value
            mock_spotify_instance.current_user.return_value = self.spotify_user_info

            # Setup mock user and friend relation
            self.mock_user.objects.get.return_value = User(user_id=self.user_id)
            mock_relation = UserFriendRelation(
                user1_id=User(user_id=self.friend_user_id),
                user2_id=User(user_id=self.user_id),
            )
            self.mock_user_friend_relation.objects.filter.return_value = [mock_relation]

            # Test 'cancel' action
            url = (
                reverse("search:process_friend_request", args=[self.friend_user_id])
                + f"?action={action}"
            )
            request = self.factory.get(url)
            request.session = {}
            response = process_friend_request(request, self.friend_user_id)
            self.assertEqual(response.status_code, 200)
