from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.sessions.middleware import SessionMiddleware


class LogoutViewTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def add_session_to_request(self, request):
        """Add a session to the request object."""
        middleware = SessionMiddleware(lambda _: _)
        middleware.process_request(request)
        request.session.save()

    def test_logout_view(self):
        # Create a request object
        request = self.factory.get(
            reverse("dashboard:logout")
        )  # Replace 'logout' with your actual logout URL name

        # Manually add a session to the request
        self.add_session_to_request(request)
