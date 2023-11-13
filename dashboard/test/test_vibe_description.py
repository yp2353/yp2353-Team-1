from django.test import TestCase
from unittest.mock import patch
from dashboard.views import vibe_description


class MockOpenAIResponse:
    def __init__(self):
        self.choices = [
            {
                "message": {
                    "role": "assistant",
                    "content": "Today's music vibe is energetic and upbeat, reminiscent of artists like Bruno Mars and Pharrell Williams.",
                }
            }
        ]


class VibeDescriptionTestCase(TestCase):
    @patch("dashboard.views.openai.ChatCompletion.create")
    def test_vibe_description(self, mock_openai):
        # Setup mock response
        mock_response = MockOpenAIResponse()
        mock_openai.return_value = mock_response

        final_vibe = "energetic and upbeat"

        response = vibe_description(final_vibe)

        expected_response = "Today's music vibe is energetic and upbeat, reminiscent of artists like Bruno Mars and Pharrell Williams."
        self.assertEqual(response, expected_response)
