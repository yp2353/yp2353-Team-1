# user_profile/signals.py
from django.db.models.signals import post_migrate
from django.apps import apps


def load_user_model(sender, **kwargs):
    from user_profile.models import User  # noqa


post_migrate.connect(load_user_model, sender=apps.get_app_config("user_profile"))
