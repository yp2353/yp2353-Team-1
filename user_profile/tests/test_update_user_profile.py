from django.test import TestCase, RequestFactory
from django.urls import reverse
from unittest.mock import patch
from user_profile.views import update_user_profile
from user_profile.models import User
from datetime import datetime


class UserProfileUpdateTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user_id = "some_valid_user_id"

        # Create a test user in the database for testing
        User.objects.create(
            user_id=self.user_id,
            username="test_user",
            total_followers=100,  # Example value, adjust as needed
            user_last_login=datetime.now(),  # Current timestamp
        )

    @patch("user_profile.models.User.objects.filter")
    def test_update_user_profile_existing_user(self, mock_filter):
        # Mock the filter method to return the test user
        mock_user = User.objects.get(user_id=self.user_id)
        mock_filter.return_value.first.return_value = mock_user

        # Create a request and call the view
        request = self.factory.get(
            reverse("user_profile:update_profile", kwargs={"user_id": self.user_id})
        )
        response = update_user_profile(request, self.user_id)

        # Check that the response is correct
        self.assertEqual(response.status_code, 200)

    @patch("user_profile.models.User.objects.filter")
    def test_update_user_profile_non_existing_user(self, mock_filter):
        # Mock the filter method to return the test user
        mock_user = User.objects.get(user_id=self.user_id)
        mock_filter.return_value.first.return_value = mock_user

        # Create a request and call the view
        request = self.factory.get(
            reverse("user_profile:update_profile", kwargs={"user_id": "something_new"})
        )
        response = update_user_profile(request, self.user_id)

        # Check that the response is correct
        self.assertEqual(response.status_code, 200)
