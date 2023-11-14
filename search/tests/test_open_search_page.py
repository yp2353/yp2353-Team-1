from django.test import TestCase, RequestFactory
from django.urls import reverse
from unittest.mock import patch, MagicMock
from search.views import open_search_page


class OpenSearchPageTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user_id = "12345"  # Mock user ID

        # Mocking Spotify API response
        self.spotify_user_info = {"id": self.user_id}

        # Mocking the database models
        self.mock_user_friend_relation = MagicMock()
        self.mock_user_friend_relation.objects.filter.return_value = []

    def test_open_search_page_with_token(self):
        with patch("search.views.get_spotify_token") as mock_get_spotify_token, patch(
            "search.views.spotipy.Spotify"
        ) as mock_spotify, patch(
            "search.views.UserFriendRelation", new=self.mock_user_friend_relation
        ):
            # Setup mock for Spotify token
            mock_get_spotify_token.return_value = {"access_token": "mock_token"}

            # Setup mock for Spotify API response
            mock_spotify_instance = mock_spotify.return_value
            mock_spotify_instance.current_user.return_value = self.spotify_user_info

            # Create a request object
            request = self.factory.get(reverse("search:search_page"))
            request.session = {}

            # Call the view
            response = open_search_page(request)

            # Check the response
            self.assertEqual(response.status_code, 200)

        #    self.assertIsInstance(response.context_data['UsersearchForm'], UsersearchForm)
        #    self.assertIn('request_list', response.context_data)
        #    self.assertIn('friends', response.context_data)

    @patch("search.views.get_spotify_token")
    def test_open_search_page_without_token(self, mock_get_spotify_token):
        # Setup mock to return None, indicating no token
        mock_get_spotify_token.return_value = None

        # Create a request object
        request = self.factory.get(reverse("search:search_page"))
        request.session = {}

        # Call the view
        response = open_search_page(request)

        # Check the response
        self.assertEqual(
            response.status_code, 302
        )  # 302 is the status code for a redirect
        self.assertTrue(
            response.url.startswith(reverse("login:index"))
        )  # Check if it redirects to login page
