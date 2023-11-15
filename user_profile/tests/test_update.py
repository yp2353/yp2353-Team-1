from django.test import TestCase, RequestFactory
from django.urls import reverse
from user_profile.models import User
from user_profile.views import update


class UpdateViewTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user_id = "test_user_id"
        User.objects.create(
            user_id=self.user_id,
            username="test_user",
            total_followers=100,
            user_last_login="2023-01-01",
        )

    def test_update_view_post_request(self):
        # Testing POST request with both bio and city
        request = self.factory.post(
            reverse("user_profile:update", args=[self.user_id]),
            {"user_bio": "New Bio", "user_city": "New City"},
        )
        response = update(request, self.user_id)

        user = User.objects.get(user_id=self.user_id)
        self.assertEqual(user.user_bio, "New Bio")
        self.assertEqual(user.user_city, "New City")
        self.assertEqual(response.status_code, 302)  # Check for redirect
        self.assertEqual(response.url, reverse("user_profile:profile_page"))

    def test_update_view_post_request_partial_data(self):
        # Testing POST request with only one field (e.g., bio)
        request = self.factory.post(
            reverse("user_profile:update", args=[self.user_id]),
            {"user_bio": "Updated Bio"},
        )
        response = update(request, self.user_id)

        user = User.objects.get(user_id=self.user_id)
        self.assertEqual(user.user_bio, "Updated Bio")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("user_profile:profile_page"))

    def test_update_view_non_post_request(self):
        # Testing non-POST request (e.g., GET)
        request = self.factory.get(reverse("user_profile:update", args=[self.user_id]))
        response = update(request, self.user_id)

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("user_profile:profile_page"))
