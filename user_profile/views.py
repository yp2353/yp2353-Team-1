from django.shortcuts import render
from django.contrib.auth.decorators import login_required
import supabase

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
        user = vibe = profile_image_url = None

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
            vibe = Vibe(user_id=user_id, user_vibe="happy", vibe_time=time)
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
            vibe = Vibe(user_id=user_id, user_vibe="happy", vibe_time=time)
            vibe.save()
            user.save()

        context = {
            "user": user,
            "vibe": vibe,
            "default_image_path": "user_profile/blank_user_profile_image.jpeg",
        }
        return render(request, "user_profile/user_profile.html", context)
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")


def update_user_profile(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id")
        user = User.objects.filter(user_id=user_id).first()
        context = {"user": user}
        return render(request, "user_profile/update_profile.html", context)


def update(request):
    print("Updating....")
    user_id = request.POST.get("user_id")
    user = User.objects.filter(user_id=user_id).first()
    user.user_bio = request.POST.get("user_bio")
    user.user_city = request.POST.get("user_city")
    new_profile_image = request.POST.get("profile_image")
    print(new_profile_image)

    print(f"user-> {user.user_bio}")
    print(f"city-> {user.user_city}")

    user.save()

    context = {"user": user}
    return redirect("user_profile:profile_page")


def upload_user_image(user, image_file):
    # Upload the image to Supabase storage
    response = supabase.storage.from_path(
        f"users/{user.user_id}/profile_image", image_file
    )
    if response.get("error"):
        raise Exception(f"Failed to upload image: {response['error']}")

    # Store the URL in the user's profile_image_url field
    user.profile_image_url = response["data"]["URL"]
    user.save()
