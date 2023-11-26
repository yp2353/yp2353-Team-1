from django.shortcuts import render, redirect

# from django.contrib.auth.decorators import login_required
from dotenv import load_dotenv
from .models import User
from django.contrib import messages

# Load variables from .env
load_dotenv()

# Create your views here.


def check_and_store_profile(request):
    # Check if the user is authenticated
    if request.user.is_authenticated:
        user = request.user

        context = {
            "username": user.username,
            "user": user,
            "default_image_path": "user_profile/blank_user_profile_image.jpeg",
        }
        return render(request, "user_profile/user_profile.html", context)
    else:
        # No token, redirect to login again
        print("User Missing!!!!!")
        messages.error(
            request,
            "Check_and_store_profile failed, please try again later. User unavailable.",
        )
        return redirect("login:index")


def edit(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id", None)

        if user_id is not None:
            user = User.objects.filter(user_id=user_id).first()

            if not user:
                # User doesnt exist in database?
                messages.error(
                    request,
                    "Edit profile failed, please try again later. User unavailable.",
                )
                return redirect("login:index")

            context = {
                "username": user.username,
                "user": user,
            }
            return render(request, "user_profile/update_profile.html", context)

    messages.error(request, "Edit profile failed, please try again later.")
    return redirect("login:index")


def update(request):
    if request.method == "POST":
        user_id = request.POST.get("user_id", None)

        if user_id is not None:
            user = User.objects.filter(user_id=user_id).first()

            if not user:
                # User doesnt exist in database?
                messages.error(
                    request,
                    "Update profile failed, please try again later. User unavailable.",
                )
                return redirect("login:index")

            bio = request.POST.get("user_bio", None)
            city = request.POST.get("user_city", None)

            if city:
                user.user_city = city
            if bio != user.user_bio:
                user.user_bio = bio
            user.save()

            return redirect("user_profile:profile_page")

    messages.error(request, "Edit profile failed, please try again later.")
    return redirect("login:index")
