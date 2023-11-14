from django.test import TestCase
from test_utils import load_test_data


class UserProfileTest(TestCase):
    def setUp(self):
        load_test_data()
