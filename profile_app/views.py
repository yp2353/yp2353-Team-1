from django.shortcuts import redirect, render

import spotipy
from utils import get_spotify_token
from django.utils import timezone
from .models import User

# Create your views here.


def check_and_store_profile(request):
    token_info = get_spotify_token(request)

    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])
        user = None
        user_info = sp.current_user()
        user_id = user_info["id"]
        user_exists = User.objects.filter(user_id=user_id).exists()
        if not user_exists:
            profile_image_url = (
                user_info["images"][0]["url"]
                if ("images" in user_info and user_info["images"])
                else None
            )
            user_country = user_info["country"] if (user_info["country"]) else None

            user = User(
                user_id=user_id,
                username=user_info["display_name"],
                total_followers=user_info["followers"]["total"],
                profile_image_url=profile_image_url,
                user_country=user_country,  # To get country detail we need to update scope of API
                user_vibe="happy",  # currently set to Happy
                user_last_login=timezone.now(),
            )
            user.save()
        else:
            user = User.objects.get(user_id=user_id)
            user.user_last_login = timezone.now()
            user.save()

        context = {"user": user}
        return render(request, "profile_app/profile.html", context)
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")
