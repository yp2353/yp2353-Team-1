from django.shortcuts import redirect, render
from django.utils import timezone
from user_profile.models import Vibe, User, UserFriendRelation
import numpy as np
from vibematch.models import UserLocation
import re
from dashboard.models import EmotionVector, Track, Artist
from django.db.models import OuterRef, Subquery, F
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from django.contrib.auth.decorators import login_required
from math import radians, cos, sin, asin, sqrt
import math
from django.db.models import Q


def vibe_match(request):
    if request.user.is_authenticated:
        user_info = request.user
        user_id = user_info.user_id
        # Pass username to navbar
        username = user_info.username

        nearest_neighbors_ids, all_users, physical_distances = k_nearest_neighbors(
            6, user_id
        )

        matches = []
        for uid, _ in nearest_neighbors_ids:
            this_user = User.objects.get(user_id=uid)

            matches.append(
                {
                    "user_id": uid,
                    "username": this_user,
                    "vibe": all_users.filter(user_id=uid)
                    .values_list("user_lyrics_vibe", "user_audio_vibe", flat=False)
                    .first(),
                    "distance": math.ceil(physical_distances.get(uid, None))
                    if physical_distances.get(uid) is not None
                    else None,
                    "similarity": distance_to_similarity(_),
                }
            )

        context = {
            "neighbors": matches,
            "username": username,
        }

        return render(request, "match.html", context)
    else:
        # No token, redirect to login again
        messages.error(request, "Vibe_match failed, please try again later.")
        return redirect("login:index")


def k_nearest_neighbors(k, target_user_id):
    # Get the most recent vibe for each user
    # Subquery to get the latest vibe_time for each user
    latest_vibe_times = (
        Vibe.objects.filter(user_id=OuterRef("user_id"))
        .order_by("-vibe_time")
        .values("vibe_time")[:1]
    )

    # Filter Vibe objects to only get those matching the latest vibe_time for each user
    latest_vibes = Vibe.objects.annotate(
        latest_vibe_time=Subquery(latest_vibe_times)
    ).filter(vibe_time=F("latest_vibe_time"))

    all_users, physical_distances = get_users(target_user_id, latest_vibes)

    # Fetch Emotion Vectors
    lyrics_vibe_values = list(set(user[1] for user in all_users))
    audio_vibe_values = list(set(user[2] for user in all_users))
    all_vibe_values = list(set(lyrics_vibe_values + audio_vibe_values))

    need_emotion_vectors = EmotionVector.objects.filter(
        emotion__in=[value for value in all_vibe_values]
    )

    emotion_vectors = {
        str(emotion.emotion): vector_to_array(emotion.vector)
        for emotion in need_emotion_vectors
    }

    all_users_array = []
    target_user_features = None

    for user in all_users:
        user_id, lyrics_vibe, audio_vibe, *features = user
        lyrics_vector = emotion_vectors.get(
            lyrics_vibe, np.zeros_like(next(iter(emotion_vectors.values())))
        )
        audio_vector = emotion_vectors.get(
            audio_vibe, np.zeros_like(next(iter(emotion_vectors.values())))
        )
        features = [float(feature) for feature in features]

        if user_id != target_user_id:
            # Check friend relation status here.
            # Do not want to recommend people you are already friends
            # or have a pending friend request with

            friend_request = UserFriendRelation.objects.filter(
                (Q(user1_id=user_id) & Q(user2_id=target_user_id))
                | (Q(user2_id=user_id) & Q(user1_id=target_user_id))
            ).first()

            if not friend_request or friend_request.status == "not_friend":
                # Friend request does not exist or there's a row in table but not friends anymore
                all_users_array.append(
                    (user_id, [*lyrics_vector, *audio_vector, *features])
                )

        else:
            target_user_features = [*lyrics_vector, *audio_vector, *features]

    if target_user_features is None:
        return []

    # Calculate distances, excluding the target user
    distances = [
        (user_id, euclidean_distance(target_user_features, features))
        for user_id, features in all_users_array
    ]

    # Sort by distance and select top k
    nearest_neighbors_ids = sorted(distances, key=lambda x: x[1])[:k]

    return nearest_neighbors_ids, all_users, physical_distances


def distance_to_similarity(distance):
    return math.ceil((1 / (1 + distance)) * 100)


def get_users(target_user_id, latest_vibes):
    today = timezone.localdate()
    phys_distances = {}

    # Check if a location for today already exists
    if UserLocation.objects.filter(
        user=User.objects.get(user_id=target_user_id), created_at__date=today
    ).exists():
        # Filter for users within 60 miles of the target user
        # Getting latest location for each user
        all_user_locations = UserLocation.objects.filter(
            created_at=Subquery(
                UserLocation.objects.filter(user=OuterRef("user"))
                .order_by("-created_at")
                .values("created_at")[:1]
            )
        )

        nearby_users, phys_distances = get_nearby_users(
            all_user_locations, target_user_id
        )

        all_users = latest_vibes.filter(user_id__in=nearby_users).values_list(
            "user_id",
            "user_lyrics_vibe",
            "user_audio_vibe",
            "user_acousticness",
            "user_danceability",
            "user_energy",
            "user_valence",
            flat=False,
        )
    else:
        # If no location for the target user, use the existing method
        all_users = latest_vibes.values_list(
            "user_id",
            "user_lyrics_vibe",
            "user_audio_vibe",
            "user_acousticness",
            "user_danceability",
            "user_energy",
            "user_valence",
            flat=False,
        )

    return all_users, phys_distances


def get_nearby_users(all_user_locations, target_user_id):
    # Get target user's location
    target_user_location = (
        UserLocation.objects.filter(user_id=target_user_id)
        .order_by("-created_at")
        .first()
    )

    nearby_users = []
    user_distances = {}
    for location in all_user_locations:
        distance = haversine(
            target_user_location.longitude,
            target_user_location.latitude,
            location.longitude,
            location.latitude,
        )
        if distance <= 60:
            nearby_users.append(location.user_id)
            user_distances[location.user_id] = distance

    return nearby_users, user_distances


def euclidean_distance(user_1, user_2):
    user_1 = np.array(user_1)
    user_2 = np.array(user_2)
    return np.sqrt(np.sum((user_1 - user_2) ** 2))


def vector_to_array(vector_str):
    clean = re.sub(r"[\[\]\n\t]", "", vector_str)
    clean = clean.split()
    clean = [float(e) for e in clean]
    return np.array(clean)


# Haversine formula to calculate distance between two lat/long points
def haversine(lon1, lat1, lon2, lat2):
    # Convert decimal degrees to radians
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * asin(sqrt(a))
    r = 3956  # Radius of Earth in miles
    return c * r


@csrf_exempt
@require_http_methods(["POST"])
def store_location(request):
    if not request.user.is_authenticated:
        return JsonResponse({"status": "unauthorized"}, status=401)

    # Get today's date
    today = timezone.localdate()

    # Check if a location for today already exists
    if UserLocation.objects.filter(user=request.user, created_at__date=today).exists():
        # If it does, return a success response without creating a new entry
        return JsonResponse({"status": "location already stored for today"}, status=200)

    try:
        data = json.loads(request.body)
        latitude = data["latitude"]
        longitude = data["longitude"]

        # Create a new UserLocation instance and save it to the database
        UserLocation.objects.create(
            user=request.user, latitude=latitude, longitude=longitude
        )

        return JsonResponse({"status": "success"}, status=200)
    except (KeyError, json.JSONDecodeError, TypeError) as e:
        # Return an error message if something goes wrong
        return JsonResponse({"status": "error", "message": str(e)}, status=400)


@login_required
def check_location_stored(request):
    today = timezone.localdate()
    location_exists = UserLocation.objects.filter(
        user=request.user, created_at__date=today
    ).exists()
    return JsonResponse({"locationStored": location_exists})
