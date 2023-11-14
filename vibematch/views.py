from django.http import HttpResponse
from django.shortcuts import redirect
from utils import get_spotify_token
import spotipy
from user_profile.models import Vibe
import numpy as np


def vibe_match(request):
    token_info = get_spotify_token(request)
    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        user_id = user_info["id"]
        matches = k_nearest_neighbors(1, user_id)

        return HttpResponse(matches)
    else:
        # No token, redirect to login again
        # ERROR MESSAGE HERE?
        return redirect("login:index")


def k_nearest_neighbors(k, target_user_id):
    # Convert the entire dataset to a NumPy array just once
    all_users = Vibe.objects.values_list(
        "user_id",
        "user_acousticness",
        "user_danceability",
        "user_energy",
        "user_valence",
        flat=False,
    )

    all_users_array = np.array(list(all_users))

    # Find the index of the target user in the array
    target_index = next(
        (i for i, v in enumerate(all_users_array) if v[0] == target_user_id), None
    )

    # Check if target user exists in the dataset
    if target_index is None:
        return []

    # Extract the target user's features
    target_user_features = all_users_array[target_index, 1:]

    # Calculate distances from the target user to all other users
    distances = np.array(
        [
            euclidean_distance(target_user_features, user[1:])
            for i, user in enumerate(all_users_array)
            if i != target_index
        ]
    )

    # Get the indices of the k smallest distances
    nearest_indices = np.argsort(distances)[:k]

    # Double-check to exclude target user
    nearest_indices = [i for i in nearest_indices if i != target_index][:k]

    # Retrieve the user_ids of the k-nearest neighbors
    nearest_neighbors = [all_users_array[i][0] for i in nearest_indices]

    return nearest_neighbors


def euclidean_distance(user_1, user_2):
    return np.sqrt(np.sum((user_1 - user_2) ** 2))
