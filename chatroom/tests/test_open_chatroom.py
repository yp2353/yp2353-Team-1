from django.test import TestCase, Client
from unittest.mock import patch
from django.urls import reverse
from chatroom.models import User, RoomModel
from django.utils import timezone


class OpenChatroomTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create(
            user_id="test_user_id",
            username="test_username",
            total_followers=0,
            profile_image_url=None,
            user_country=None,
            user_last_login=timezone.now(),
            user_bio=None,
            user_city=None,
            user_total_friends=None,
        )
        self.room = RoomModel.objects.create(roomID="global_room")
        self.room.room_participants.add(self.user)

    @patch("chatroom.views.get_spotify_token")
    @patch("spotipy.Spotify")
    def test_open_chatroom(self, mock_spotify, mock_get_token):
        mock_get_token.return_value = {"access_token": "test_token"}
        mock_spotify.return_value.current_user.return_value = {
            "id": "test_user_id",
            "display_name": "test_user",
        }

        response = self.client.get(reverse("chatroom:open_chatroom"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "chatroom/chatroom.html")
        self.assertEqual(response.context["username"], "test_user")
        self.assertEqual(response.context["user"], self.user)
        self.assertEqual(list(response.context["rooms_list"]), [self.room])

    @patch("chatroom.views.get_spotify_token")
    def test_open_chatroom_no_token(self, mock_get_token):
        mock_get_token.return_value = None

        response = self.client.get(reverse("chatroom:open_chatroom"))

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("login:index"))
