from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from user_profile.models import User, UserFriendRelation
from django.utils import timezone


class ProcessFriendRequestTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        # Create User instances with all required fields
        self.user1 = User.objects.create(
            user_id="user1",
            username="username1",
            total_followers=10,
            user_last_login=timezone.now(),
            # Add other fields as required
        )
        self.user2 = User.objects.create(
            user_id="friend_user_id",
            username="username2",
            total_followers=15,
            user_last_login=timezone.now(),
            # Add other fields as required
        )

    @patch("search.views.get_spotify_token")
    @patch("search.views.spotipy.Spotify")
    def test_send_new_friend_request(self, mock_spotify, mock_get_token):
        """
        Test sending a new friend request where none existed before.
        """
        mock_get_token.return_value = {"access_token": "fake_token"}
        mock_spotify_instance = MagicMock()
        mock_spotify.return_value = mock_spotify_instance
        mock_spotify_instance.current_user.return_value = {
            "id": "user1",
            "display_name": "username1",
        }

        response = self.client.get(
            reverse("search:process_friend_request", args=["friend_user_id"]),
            {"action": "send"},
        )
        self.assertEqual(response.status_code, 200)
        # Assertions to verify the creation of a new friend request

    @patch("search.views.get_spotify_token")
    @patch("search.views.spotipy.Spotify")
    def test_send_friend_request(self, mock_spotify, mock_get_token):
        mock_get_token.return_value = {"access_token": "fake_token"}
        mock_spotify_instance = MagicMock()
        mock_spotify.return_value = mock_spotify_instance
        mock_spotify_instance.current_user.return_value = {
            "id": "user1",
            "display_name": "username1",
        }

        # Ensure no existing friend request
        response = self.client.get(
            reverse("search:process_friend_request", args=[self.user2.user_id]),
            {"action": "send"},
        )
        self.assertEqual(response.status_code, 200)
        try:
            friend_request = UserFriendRelation.objects.get(
                user1_id=self.user1, user2_id=self.user2
            )
            self.assertEqual(friend_request.status, "pending")
        except UserFriendRelation.DoesNotExist:
            self.fail("UserFriendRelation object not created after sending request")

    # @patch("search.views.get_spotify_token")
    # @patch("search.views.spotipy.Spotify")
    # def test_cancel_friend_request(self, mock_spotify, mock_get_token):
    #     mock_get_token.return_value = {"access_token": "fake_token"}
    #     mock_spotify_instance = MagicMock()
    #     mock_spotify.return_value = mock_spotify_instance
    #     mock_spotify_instance.current_user.return_value = {
    #         "id": "user1",
    #         "display_name": "username1",
    #     }

    #     friend_request = UserFriendRelation.objects.create(
    #         user1_id=self.user1, user2_id=self.user2, status="pending"
    #     )
    #     response = self.client.get(
    #         reverse("search:process_friend_request", args=[self.user2.user_id]),
    #         {"action": "cancel"},
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     friend_request.refresh_from_db()
    #     self.assertEqual(friend_request.status, "cancle_request")

    @patch("search.views.get_spotify_token")
    @patch("search.views.spotipy.Spotify")
    def test_unfriend_friend_request(self, mock_spotify, mock_get_token):
        mock_get_token.return_value = {"access_token": "fake_token"}
        mock_spotify_instance = MagicMock()
        mock_spotify.return_value = mock_spotify_instance
        mock_spotify_instance.current_user.return_value = {
            "id": "user1",
            "display_name": "username1",
        }

        friend_request = UserFriendRelation.objects.create(
            user1_id=self.user1, user2_id=self.user2, status="friends"
        )
        response = self.client.get(
            reverse("search:process_friend_request", args=[self.user2.user_id]),
            {"action": "unfriend"},
        )
        self.assertEqual(response.status_code, 200)
        friend_request = UserFriendRelation.objects.get(
            user1_id=self.user1, user2_id=self.user2
        )
        self.assertEqual(friend_request.status, "not_friend")

    @patch("search.views.get_spotify_token")
    @patch("search.views.spotipy.Spotify")
    def test_accept_friend_request(self, mock_spotify, mock_get_token):
        mock_get_token.return_value = {"access_token": "fake_token"}
        mock_spotify_instance = MagicMock()
        mock_spotify.return_value = mock_spotify_instance
        mock_spotify_instance.current_user.return_value = {
            "id": "user1",
            "display_name": "username1",
        }

        # Setup a pending friend request
        friend_request = UserFriendRelation.objects.create(
            user1_id=self.user2, user2_id=self.user1, status="pending"
        )
        response = self.client.get(
            reverse("search:process_friend_request", args=[self.user2.user_id]),
            {"action": "accept"},
        )
        self.assertEqual(response.status_code, 200)
        friend_request = UserFriendRelation.objects.get(
            user1_id=self.user2, user2_id=self.user1
        )
        self.assertEqual(friend_request.status, "friends")

    # @patch("search.views.get_spotify_token")
    # @patch("search.views.spotipy.Spotify")
    # def test_decline_friend_request(self, mock_spotify, mock_get_token):
    #     mock_get_token.return_value = {"access_token": "fake_token"}
    #     mock_spotify_instance = MagicMock()
    #     mock_spotify.return_value = mock_spotify_instance
    #     mock_spotify_instance.current_user.return_value = {
    #         "id": "user1",
    #         "display_name": "username1",
    #     }

    #     UserFriendRelation.objects.create(
    #         user1_id=self.user2, user2_id=self.user1, status="pending"
    #     )
    #     response = self.client.get(
    #         reverse("search:process_friend_request", args=[self.user2.user_id]),
    #         {"action": "decline"},
    #     )
    #     self.assertEqual(response.status_code, 200)
    #     friend_request = UserFriendRelation.objects.get(
    #         user1_id=self.user2, user2_id=self.user1
    #     )
    #     self.assertEqual(friend_request.status, "decline")
