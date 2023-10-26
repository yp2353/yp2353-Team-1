from django.shortcuts import redirect, render
# from django.contrib.auth.decorators import login_required
import supabase
import os
from dotenv import load_dotenv
import spotipy
from utils import get_spotify_token
from django.utils import timezone
from .models import User, Vibe

# Load variables from .env
load_dotenv()


def check_and_store_profile(request):
    token_info = get_spotify_token(request)

    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])
        user = vibe = profile_image_url = None

        time = timezone.now()
        user_info = sp.current_user()
        user_id = user_info["id"]
        user_exists = User.objects.filter(user_id=user_id).first()

        if not user_exists:
            profile_image_url = (
                user_info["images"][0]["url"]
                if ("images" in user_info and user_info["images"])
                else None
            )
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
            if user.profile_image_url:
                user.profile_image_url = get_profile_image_url(user_id)
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
    user_id = request.POST.get("user_id")
    user = User.objects.filter(user_id=user_id).first()

    bio = request.POST.get("user_bio")
    city = request.POST.get("user_city")
    new_profile_image = request.FILES.get("profile_image")
    print(new_profile_image)
    if city:
        user.user_city = city
    if bio != user.user_bio:
        user.user_bio = bio
    if new_profile_image:
        user.profile_image_url = upload_user_image(user, new_profile_image)
        print(user.profile_image_url)
    else:
        print("No Image added")
    user.save()

    return redirect("user_profile:profile_page")


def upload_user_image(user, image_file):
    print("image upload started...")

    # Convert the Image to bytes
    image_bytes = image_file.read()

    # Upload the image to Supabase storage
    SUPABSE_URL = os.getenv("SUPABSE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase_client = supabase.Client(SUPABSE_URL, SUPABASE_KEY)

    bucket_name = "user_profile_pic"
    file_path = f"{bucket_name}/users/{user.user_id}"  # Define your own path as needed

    supabase_client.storage.from_(bucket_name).remove(
        file_path
    )  # delete previous image

    supabase_client.storage.from_(bucket_name).upload(
        file_path, image_bytes
    )  # add new to Storage

    response = supabase_client.storage.from_(bucket_name).create_signed_url(
        file_path, 20000
    )

    print(response)
    if response.get("error"):
        raise Exception(f"Failed to upload image: {response['error']}")
    return response.get("signedURL")


def get_profile_image_url(user_id):
    # Upload the image to Supabase storage
    SUPABSE_URL = os.getenv("SUPABSE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    supabase_client = supabase.Client(SUPABSE_URL, SUPABASE_KEY)

    bucket_name = "user_profile_pic"
    file_path = f"{bucket_name}/users/{user_id}"  # Define your own path as needed

    response = supabase_client.storage.from_(bucket_name).create_signed_url(
        file_path, 20000
    )

    print(response)
    if response.get("error"):
        raise Exception(f"Failed to Get URL image: {response['error']}")
    return response.get("signedURL")
