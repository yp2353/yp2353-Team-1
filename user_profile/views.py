from django.shortcuts import render

# Create your views here.
from django.shortcuts import redirect, render

import spotipy
from utils import get_spotify_token
from django.utils import timezone
from .models import User, Vibe

# Create your views here.


def check_and_store_profile(request):
    token_info = get_spotify_token(request)

    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])
        user = vibe = profile_image_url  = None
        
        time = timezone.now()

        user_info = sp.current_user()
        user_id = user_info["id"]
        profile_image_url = (
                user_info["images"][0]["url"]
                if ("images" in user_info and user_info["images"])
                else None
            )
        user_exists = User.objects.filter(user_id=user_id).first()

        if not user_exists:
            
            user = User(
                user_id=user_id,
                username=user_info["display_name"],
                total_followers=user_info["followers"]["total"],
                profile_image_url=profile_image_url,
                user_country=user_info["country"], 
                user_last_login=time,
            )
            vibe = Vibe(
                user_id = user_id,
                user_vibe = "happy",
                vibe_time = time
            )
            vibe.save()
            user.save()
        else:
            user = user_exists

            if user.username != user_info["display_name"]:
                user.username = user_info["display_name"]
            if user.total_followers != user_info["followers"]["total"]:
                user.total_followers = user_info["followers"]["total"]
            if user.profile_image_url != profile_image_url:
                user.profile_image_url = profile_image_url
            if user.user_country != user_info["country"]:
                user.user_country = user_info["country"]

            user.user_last_login = timezone.now()
            vibe = Vibe(
                user_id = user_id,
                user_vibe = "happy",
                vibe_time = time
            )
            vibe.save()
            user.save()

        context = {
            "user": user,
            "vibe": vibe,
        }
        return render(request, "user_profile/user_profile.html", context)
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")
