from django.test import TestCase
from user_profile.models import (
    User,
    UserFriendRelation,
)  # Replace with your actual import paths
from search.views import current_friend_list  # Replace with your actual import path
import datetime


class CurrentFriendListTests(TestCase):
    def setUp(self):
        # Create test users
        self.user1 = User.objects.create_user(
            username="user1",
            password="password",
            user_id="user1_id",
            total_followers=100,
            profile_image_url="http://example.com/image.jpg",
            user_country="Test Country",
            user_last_login=datetime.datetime.now(),
            user_bio="Test Bio",
            user_city="Test City",
            user_total_friends=50,
            track_id="track123",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            password="password",
            user_id="user2_id",
            total_followers=100,
            profile_image_url="http://example.com/image.jpg",
            user_country="Test Country",
            user_last_login=datetime.datetime.now(),
            user_bio="Test Bio",
            user_city="Test City",
            user_total_friends=50,
            track_id="track123",
        )
        self.user3 = User.objects.create_user(
            username="user3",
            password="password",
            user_id="user3_id",
            total_followers=100,
            profile_image_url="http://example.com/image.jpg",
            user_country="Test Country",
            user_last_login=datetime.datetime.now(),
            user_bio="Test Bio",
            user_city="Test City",
            user_total_friends=50,
            track_id="track123",
        )

        # Create test friend relationships
        UserFriendRelation.objects.create(
            user1_id=self.user1, user2_id=self.user2, status="friends"
        )
        UserFriendRelation.objects.create(
            user1_id=self.user1, user2_id=self.user3, status="friends"
        )
        # Create a non-friend relationship for testing
        UserFriendRelation.objects.create(
            user1_id=self.user2, user2_id=self.user3, status="pending"
        )

    def test_current_friend_list(self):
        friends_of_user1 = current_friend_list("user1_id")
        self.assertIn(self.user2, friends_of_user1)
        self.assertIn(self.user3, friends_of_user1)
        self.assertEqual(len(friends_of_user1), 2)

        friends_of_user2 = current_friend_list("user2_id")
        self.assertIn(self.user1, friends_of_user2)
        self.assertNotIn(
            self.user3, friends_of_user2
        )  # user3 should not be in user2's friend list
        self.assertEqual(len(friends_of_user2), 1)
