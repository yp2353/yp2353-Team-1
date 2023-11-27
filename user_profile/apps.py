# user_profile/apps.py
from django.apps import AppConfig


class UserProfileConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "user_profile"

    def ready(self):
        # Import signals module to ensure they are connected
        import user_profile.signals  # noqa
