from django.test import TestCase, RequestFactory

# from django.urls import reverse
# from unittest.mock import patch
from unittest.mock import MagicMock

# from search.views import user_search

# from user_profile.models import User, Vibe, UserTop, UserFriendRelation
# from search.forms import   # Replace with actual form import


class UserSearchTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user_id = "12345"  # Mock user ID

        # Mocking Spotify API response
        self.spotify_user_info = {"id": self.user_id}

        # Mocking the database models
        self.mock_user = MagicMock()
        self.mock_user_friend_relation = MagicMock()
        self.mock_user.objects.filter.return_value = []

    # def test_user_search_with_valid_token_and_form(self):
    #     with patch("search.views.get_spotify_token") as mock_get_spotify_token, patch(
    #         "search.views.spotipy.Spotify"
    #     ) as mock_spotify, patch("user_profile.models.User", new=self.mock_user), patch(
    #         "user_profile.models.UserFriendRelation", new=self.mock_user_friend_relation
    #     ):
    #         # Setup mock for Spotify token
    #         mock_get_spotify_token.return_value = {"access_token": "mock_token"}

    #         # Setup mock for Spotify API response
    #         mock_spotify_instance = mock_spotify.return_value
    #         mock_spotify_instance.current_user.return_value = self.spotify_user_info

    #         # Create a request object
    #         request = self.factory.get(
    #             reverse("search:search_user"), {"username": "testuser"}
    #         )
    #         request.session = {}

    #         # Call the view
    #         response = user_search(request)

    #         # Check the response
    #         self.assertEqual(response.status_code, 200)
    #         # self.assertIsInstance(response.context['UsersearchForm'], UsersearchForm)
    #         # self.assertIn('results', response.context)
