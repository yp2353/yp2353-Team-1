from django.shortcuts import redirect, render
from utils import get_spotify_token
import spotipy
from user_profile.models import Vibe, User
import numpy as np
from django.db.models import Max, F


def vibe_match(request):
    token_info = get_spotify_token(request)
    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        user_id = user_info["id"]
        matches = k_nearest_neighbors(1, user_id)

        context = {"user": matches[0]}

        return render(request, "match.html", context)
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")


def k_nearest_neighbors(k, target_user_id):
    # Get the most recent vibe for each user
    latest_vibes = Vibe.objects.annotate(max_vibe_time=Max("vibe_time")).filter(
        vibe_time=F("max_vibe_time")
    )

    # Join the latest vibes with the User model
    all_users = latest_vibes.filter(
        user_id__in=User.objects.all().values_list("user_id", flat=True)
    ).values_list(
        "user_id",
        "user_acousticness",
        "user_danceability",
        "user_energy",
        "user_valence",
        "vibe_time",
        flat=False,
    )

    all_users_array = np.array(list(all_users))

    # Find the index of the target user in the array
    target_index = next(
        (i for i, v in enumerate(all_users_array) if v[0] == target_user_id), None
    )

    if target_index is None:
        return []

    target_user_features = all_users_array[
        target_index, 1:5
    ]  # Exclude the vibe_time from features

    distances = np.array(
        [
            euclidean_distance(
                target_user_features, user[1:5]
            )  # Exclude the vibe_time from features
            for i, user in enumerate(all_users_array)
            if i != target_index
        ]
    )

    nearest_indices = np.argsort(distances)[:k]
    nearest_indices = [i for i in nearest_indices if i != target_index][:k]

    # Retrieve the user_ids of the k-nearest neighbors
    nearest_neighbors_ids = [all_users_array[i][0] for i in nearest_indices]

    # Get usernames and last vibe times
    nearest_neighbors = [
        (User.objects.get(user_id=user_id).username)  # Get username and last vibe time
        for i, user_id in enumerate(nearest_neighbors_ids)
    ]

    return nearest_neighbors


def euclidean_distance(user_1, user_2):
    return np.sqrt(np.sum((user_1 - user_2) ** 2))
