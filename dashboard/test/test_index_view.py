from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch

# from dashboard.views import index  # Adjust the import path as necessary


class IndexViewTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.current_user_recently_played = {
            "href": "string",
            "limit": 0,
            "next": "string",
            "cursors": {"after": "string", "before": "string"},
            "total": 0,
            "items": [
                {
                    "track": {
                        "album": {
                            "album_type": "compilation",
                            "total_tracks": 9,
                            "available_markets": ["CA", "BR", "IT"],
                            "external_urls": {"spotify": "string"},
                            "href": "string",
                            "id": "2up3OPMp9Tb4dAKM2erWXQ",
                            "images": [
                                {
                                    "url": "https://i.scdn.co/image/ab67616d00001e02ff9ca10b55ce82ae553c8228",
                                    "height": 300,
                                    "width": 300,
                                }
                            ],
                            "name": "string",
                            "release_date": "1981-12",
                            "release_date_precision": "year",
                            "restrictions": {"reason": "market"},
                            "type": "album",
                            "uri": "spotify:album:2up3OPMp9Tb4dAKM2erWXQ",
                            "artists": [
                                {
                                    "external_urls": {"spotify": "string"},
                                    "href": "string",
                                    "id": "string",
                                    "name": "string",
                                    "type": "artist",
                                    "uri": "string",
                                }
                            ],
                        },
                        "artists": [
                            {
                                "external_urls": {"spotify": "string"},
                                "followers": {"href": "string", "total": 0},
                                "genres": ["Prog rock", "Grunge"],
                                "href": "string",
                                "id": "string",
                                "images": [
                                    {
                                        "url": "https://i.scdn.co/image/ab67616d00001e02ff9ca10b55ce82ae553c8228",
                                        "height": 300,
                                        "width": 300,
                                    }
                                ],
                                "name": "string",
                                "popularity": 0,
                                "type": "artist",
                                "uri": "string",
                            }
                        ],
                        "available_markets": ["string"],
                        "disc_number": 0,
                        "duration_ms": 0,
                        "explicit": False,
                        "external_ids": {
                            "isrc": "string",
                            "ean": "string",
                            "upc": "string",
                        },
                        "external_urls": {"spotify": "string"},
                        "href": "string",
                        "id": "string",
                        "is_playable": False,
                        "linked_from": {},
                        "restrictions": {"reason": "string"},
                        "name": "string",
                        "popularity": 0,
                        "preview_url": "string",
                        "track_number": 0,
                        "type": "track",
                        "uri": "string",
                        "is_local": False,
                    },
                    "played_at": "2023-11-14T12:00:00Z",
                    "context": {
                        "type": "string",
                        "href": "string",
                        "external_urls": {"spotify": "string"},
                        "uri": "string",
                    },
                }
            ],
        }

        self.audio_features = [
            {
                "danceability": 0.669,
                "energy": 0.832,
                "key": 0,
                "loudness": -5.721,
                "mode": 1,
                "speechiness": 0.0682,
                "acousticness": 0.0106,
                "instrumentalness": 0,
                "liveness": 0.0968,
                "valence": 0.7,
                "tempo": 113.035,
                "type": "audio_features",
                "id": "1WkMMavIMc4JZ8cfMmxHkI",
                "uri": "spotify:track:1WkMMavIMc4JZ8cfMmxHkI",
                "track_href": "https://api.spotify.com/v1/tracks/1WkMMavIMc4JZ8cfMmxHkI",
                "analysis_url": "https://api.spotify.com/v1/audio-analysis/1WkMMavIMc4JZ8cfMmxHkI",
                "duration_ms": 237547,
                "time_signature": 4,
            },
        ]
        self.current_user_top_tracks = {
            "items": [
                {
                    "album": {
                        "album_type": "SINGLE",
                        "artists": [
                            {
                                "external_urls": {
                                    "spotify": "https://open.spotify.com/artist/7oVNI7cJUA5f1Qvu8vQlq9"
                                },
                                "href": "https://api.spotify.com/v1/artists/7oVNI7cJUA5f1Qvu8vQlq9",
                                "id": "7oVNI7cJUA5f1Qvu8vQlq9",
                                "name": "Myuk",
                                "type": "artist",
                                "uri": "spotify:artist:7oVNI7cJUA5f1Qvu8vQlq9",
                            }
                        ],
                        "available_markets": [
                            "US",
                        ],
                        "external_urls": {
                            "spotify": "https://open.spotify.com/album/1KNgIgtKAK4kSwp7si23Mw"
                        },
                        "href": "https://api.spotify.com/v1/albums/1KNgIgtKAK4kSwp7si23Mw",
                        "id": "1KNgIgtKAK4kSwp7si23Mw",
                        "images": [
                            {
                                "height": 640,
                                "url": "https://i.scdn.co/image/ab67616d0000b2731301e3fc608b91a0a23ef06b",
                                "width": 640,
                            },
                            {
                                "height": 300,
                                "url": "https://i.scdn.co/image/ab67616d00001e021301e3fc608b91a0a23ef06b",
                                "width": 300,
                            },
                            {
                                "height": 64,
                                "url": "https://i.scdn.co/image/ab67616d000048511301e3fc608b91a0a23ef06b",
                                "width": 64,
                            },
                        ],
                        "name": "魔法",
                        "release_date": "2021-02-05",
                        "release_date_precision": "day",
                        "total_tracks": 2,
                        "type": "album",
                        "uri": "spotify:album:1KNgIgtKAK4kSwp7si23Mw",
                    },
                    "artists": [
                        {
                            "external_urls": {
                                "spotify": "https://open.spotify.com/artist/7oVNI7cJUA5f1Qvu8vQlq9"
                            },
                            "href": "https://api.spotify.com/v1/artists/7oVNI7cJUA5f1Qvu8vQlq9",
                            "id": "7oVNI7cJUA5f1Qvu8vQlq9",
                            "name": "Myuk",
                            "type": "artist",
                            "uri": "spotify:artist:7oVNI7cJUA5f1Qvu8vQlq9",
                        }
                    ],
                    "available_markets": [
                        "US",
                    ],
                    "disc_number": 1,
                    "duration_ms": 231955,
                    "explicit": False,
                    "external_ids": {"isrc": "JPU902003333"},
                    "external_urls": {
                        "spotify": "https://open.spotify.com/track/0LL0hFBywgFHO89WSp00xW"
                    },
                    "href": "https://api.spotify.com/v1/tracks/0LL0hFBywgFHO89WSp00xW",
                    "id": "0LL0hFBywgFHO89WSp00xW",
                    "is_local": False,
                    "name": "魔法",
                    "popularity": 48,
                    "preview_url": "https://p.scdn.co/mp3-preview/dbf46d7973fa0965b6edee6dded7850cb620781b?cid=a70c7a9100bd4330afa05deda868cf86",
                    "track_number": 1,
                    "type": "track",
                    "uri": "spotify:track:0LL0hFBywgFHO89WSp00xW",
                }
            ],
            "total": 50,
            "limit": 1,
            "offset": 0,
            "href": "https://api.spotify.com/v1/me/top/tracks?limit=1&offset=0",
            "next": "https://api.spotify.com/v1/me/top/tracks?limit=1&offset=1",
            "previous": None,
        }

    @patch("dashboard.views.get_spotify_token")  # Mock the get_spotify_token function
    @patch("spotipy.Spotify")  # Mock the Spotify client
    def test_index_view_with_token(self, mock_spotify, mock_get_token):
        # Setup mock Spotify API responses
        mock_sp = mock_spotify.return_value
        mock_sp.current_user.return_value = {
            "display_name": "Test User",
            "id": "testuserid",
        }

        mock_sp.current_user_recently_played.return_value = (
            self.current_user_recently_played
        )

        mock_sp.audio_features.return_value = self.audio_features

        mock_sp.current_user_top_tracks.return_value = self.current_user_top_tracks

        # Mock session data
        mock_get_token.return_value = {"access_token": "testtoken"}

        # Create a request object

        # Call the view
        response = self.client.get(reverse("dashboard:index"))

        # Check if the response is as expected
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response, "dashboard/index.html"
        )  # Check if correct template is used

    # @patch("dashboard.views.get_spotify_token")
    # def test_index_view_without_token(self, mock_get_token):
    #     # Mock session data to simulate no token
    #     mock_get_token.return_value = None

    #     # Create a request object
    #     request = self.client.get(reverse("dashboard:index"))  # Adjust the view name
    #     request.session = {}  # Set up a mock session

    #     # Call the view
    #     response = index(request)

    #     # Check if redirection happens
    #     self.assertEqual(
    #         response.status_code, 302
    #     )  # 302 is the status code for redirection
    #     self.assertTrue(
    #         response.url.startswith("/login/")
    #     )  # Check if it redirects to the login page
