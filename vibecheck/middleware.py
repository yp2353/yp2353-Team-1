from django.utils import timezone
from user_profile.models import User
from user_profile.views import get_spotify_token
import spotipy

class UserProfileMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token_info = get_spotify_token(request)

        if token_info:
            sp = spotipy.Spotify(auth=token_info["access_token"])

            time = timezone.now()

            user_info = sp.current_user()
            user_id = user_info["id"]
            user_exists = User.objects.filter(user_id=user_id).first()

            if not user_exists:
                user = User(
                    user_id=user_id,
                    username=user_info["display_name"],
                    total_followers=user_info["followers"]["total"],
                    profile_image_url=(
                        user_info["images"][0]["url"]
                        if ("images" in user_info and user_info["images"])
                        else None
                    ),
                    user_country=user_info["country"],
                    user_last_login=time,
                )
                user.save()
            else:
                user = user_exists

                if user.username != user_info["display_name"]:
                    user.username = user_info["display_name"]
                if user.total_followers != user_info["followers"]["total"]:
                    user.total_followers = user_info["followers"]["total"]
                new_profile_image_url = (
                    user_info["images"][0]["url"]
                    if ("images" in user_info and user_info["images"])
                    else None
                )
                if user.profile_image_url != new_profile_image_url:
                    user.profile_image_url = new_profile_image_url
                if user.user_country != user_info["country"]:
                    user.user_country = user_info["country"]

                user.user_last_login = time
                user.save()

            request.user = user  # Attach the user object to the request for later use
            request.session["user_id"] = user.user_id 

        response = self.get_response(request)
        return response
