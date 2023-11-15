import csv
from django.test import TestCase
from django.conf import settings
import os
from user_profile.models import User, Vibe, UserTop
import decimal
from decimal import Decimal


class UserProfileTest(TestCase):
    def setUp(self):
        assets_path = os.path.join(settings.BASE_DIR, "assets")

        # Load User data from CSV
        with open(
            os.path.join(assets_path, "test_user_profile_user_rows.csv"), newline=""
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                User.objects.create(
                    user_id=row["user_id"],
                    username=row["username"],
                    total_followers=int(row["total_followers"]),
                    profile_image_url=row["profile_image_url"],
                    user_country=row["user_country"],
                    user_last_login=row["user_last_login"],
                    user_bio=row["user_bio"],
                    user_city=row["user_city"],
                    user_total_friends=(
                        int(row["user_total_friends"])
                        if row["user_total_friends"]
                        else None
                    ),
                )

        # Load Vibe data from CSV
        with open(
            os.path.join(assets_path, "test_user_profile_vibe_rows.csv"), newline=""
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                Vibe.objects.create(
                    user_id=row["user_id"],
                    user_lyrics_vibe=row["user_lyrics_vibe"],
                    user_audio_vibe=row["user_audio_vibe"],
                    user_acousticness=self.parse_decimal(row["user_acousticness"]),
                    user_danceability=self.parse_decimal(row["user_danceability"]),
                    user_energy=self.parse_decimal(row["user_energy"]),
                    user_valence=self.parse_decimal(row["user_valence"]),
                    recent_track=row["recent_track"].split(
                        ","
                    ),  # Assuming the tracks are comma-separated
                    vibe_time=row["vibe_time"],
                )

        # Load UserTop data from CSV
        with open(
            os.path.join(assets_path, "test_user_profile_usertop_rows.csv"), newline=""
        ) as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                UserTop.objects.create(
                    user_id=row["user_id"],
                    time=row["time"],
                    recommended_tracks=row["recommended_tracks"].split(
                        ","
                    ),  # Assuming the tracks are comma-separated
                    top_track=row["top_track"].split(
                        ","
                    ),  # Assuming the tracks are comma-separated
                    top_artist=row["top_artist"].split(
                        ","
                    ),  # Assuming the artists are comma-separated
                    top_genre=row["top_genre"].split(
                        ","
                    ),  # Assuming the genres are comma-separated
                )

    def parse_decimal(self, value):
        try:
            return Decimal(value) if value else None
        except (decimal.InvalidOperation, ValueError):
            return None
