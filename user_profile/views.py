from django.shortcuts import render, redirect

# from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
import spotipy
from utils import get_spotify_token
from django.utils import timezone
from .models import User, Vibe
from django.contrib import messages

# Load variables from .env
load_dotenv()

# Create your views here.


def check_and_store_profile(request):

    # Check if the user is authenticated
    if request.user.is_authenticated:
        user = request.user

        # Get user's most recent vibe, order by descending time
        recent_vibe = Vibe.objects.filter(user_id=user.user_id).order_by("-vibe_time").first()
        
        context = {
            "username": user.username,
            "user": user,
            "vibe": recent_vibe,
            "default_image_path": "user_profile/blank_user_profile_image.jpeg",
        }
        return render(request, "user_profile/user_profile.html", context)
    else:
        # No token, redirect to login again
        print("User Missing!!!!!")
        messages.error(
            request, "Check_and_store_profile failed, please try again later. User unavailable."
        )
        return redirect("login:index")



def update_user_profile(request, user_id):
    user = User.objects.filter(user_id=user_id).first()
    # Pass username to navbar
    context = {
        "username": user.username,
        "user": user,
    }
    return render(request, "user_profile/update_profile.html", context)


# Updates the profile return to User_profile Page
def update(request, user_id):
    user = User.objects.filter(user_id=user_id).first()

    if request.method == "POST":
        print("Data is changed")
        bio = request.POST.get("user_bio")
        city = request.POST.get("user_city")
        if city:
            user.user_city = city
        if bio != user.user_bio:
            user.user_bio = bio
        user.save()

    return redirect("user_profile:profile_page")
