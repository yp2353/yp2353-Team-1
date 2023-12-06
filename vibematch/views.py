from django.shortcuts import redirect, render
from utils import get_spotify_token
from django.utils import timezone
import spotipy
from user_profile.models import Vibe, User, UserTop, UserFriendRelation
import numpy as np
from vibematch.models import UserLocation
import re
from dashboard.models import EmotionVector
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
    token_info = get_spotify_token(request)
    if token_info:
        sp = spotipy.Spotify(auth=token_info["access_token"])

        user_info = sp.current_user()
        user_id = user_info["id"]
        # Pass username to navbar
        username = user_info["display_name"]

        nearest_neighbors_ids, all_users, physical_distances = k_nearest_neighbors(
            5, user_id
        )

        matches = []
        for uid, _ in nearest_neighbors_ids:
            user_top = UserTop.objects.filter(user_id=uid).order_by("-time").first()
            if user_top and len(user_top.top_artist) > 0:
                top_artist = sp.artists(user_top.top_artist[:5])
            else:
                top_artist = None

            if user_top and len(user_top.top_track) > 0:
                top_track = sp.tracks(user_top.top_track[:3])
            else:
                top_track = None

            matches.append(
                {
                    "user_id": uid,
                    "username": User.objects.get(user_id=uid),
                    "vibe": all_users.filter(user_id=uid)
                    .values_list("user_lyrics_vibe", "user_audio_vibe", flat=False)
                    .first(),
                    "fav_track": sp.track(User.objects.get(user_id=uid).track_id)
                    if User.objects.get(user_id=uid).track_id
                    else None,
                    "distance": math.ceil(physical_distances.get(uid, None))
                    if physical_distances.get(uid) is not None
                    else None,
                    "similarity": distance_to_similarity(_),
                    "top_artist": top_artist,
                    "top_tracks": top_track,
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
    # Fetch Emotion Vectors
    emotion_vectors = {
        str(emotion.emotion).lower(): vector_to_array(emotion.vector)
        for emotion in EmotionVector.objects.all()
    }

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
        all_user_locations = UserLocation.objects.all()
        nearby_users, phys_distances = get_nearby_users(
            all_user_locations, target_user_id, today
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


def get_nearby_users(all_user_locations, target_user_id, today):
    # Get target user's location
    target_user_location = UserLocation.objects.get(
        user=User.objects.get(user_id=target_user_id), created_at__date=today
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