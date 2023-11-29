from django.utils import timezone
from utils import deduce_audio_vibe, vibe_calc_threads
import lyricsgenius
import os
import openai
import time
from gradio_client import Client
import numpy as np
import re
from dashboard.models import TrackVibe, EmotionVector
from user_profile.models import Vibe

MAX_RETRIES = 2

client = Client("https://alfredo273-vibecheck-fasttext.hf.space/", serialize=False)


def calculate_vibe_async(
    track_names, track_artists, track_ids, audio_features_list, user_id
):
    audio_vibe, lyric_vibe = check_vibe(
        track_names, track_artists, track_ids, audio_features_list
    )
    vibe_result = audio_vibe
    if lyric_vibe:
        vibe_result += " " + lyric_vibe

    current_time = timezone.now().astimezone(timezone.utc)
    description = vibe_description(vibe_result)
    vibe_data = Vibe(
        user_id=user_id,
        vibe_time=current_time,
        user_lyrics_vibe=lyric_vibe,
        user_audio_vibe=audio_vibe,
        recent_track=track_ids,
        user_acousticness=get_feature_average(audio_features_list, "acousticness"),
        user_danceability=get_feature_average(audio_features_list, "danceability"),
        user_energy=get_feature_average(audio_features_list, "energy"),
        user_valence=get_feature_average(audio_features_list, "valence"),
        description=description,
    )
    vibe_data.save()

    # Thread is finished calculating, delete from current thread dictionary
    vibe_calc_threads.pop(user_id, None)


def check_vibe(track_names, track_artists, track_ids, audio_features_list):
    # Calculate the overall audio vibe for the list of tracks
    audio_final_vibe = deduce_audio_vibe(audio_features_list)

    # Fetch existing vibes from the database
    existing_vibes = TrackVibe.objects.filter(track_id__in=track_ids)
    existing_vibes_dict = {vibe.track_id: vibe for vibe in existing_vibes}

    # Determine tracks that need processing for lyrics vibes
    tracks_needing_lyrics = []
    for track_name, track_artist, track_id in zip(
        track_names, track_artists, track_ids
    ):
        track_vibe = existing_vibes_dict.get(track_id)
        if not track_vibe or track_vibe.track_lyrics_vibe is None:
            tracks_needing_lyrics.append((track_name, track_artist, track_id))

    # Process lyrics vibes if needed
    if tracks_needing_lyrics:
        names, artists, ids = zip(*tracks_needing_lyrics)
        lyrics_vibes = deduce_lyrics(names, artists, ids)
        lyrics_final_vibe = lyrics_vectorize(lyrics_vibes)
    else:
        lyrics_final_vibe = None

    # Update the database with the newly computed vibes
    for index, track_id in enumerate(track_ids):
        track_vibe = existing_vibes_dict.get(track_id, TrackVibe(track_id=track_id))

        # Update lyrics vibe if needed
        if track_id in [id for _, _, id in tracks_needing_lyrics]:
            track_vibe.track_lyrics_vibe = lyrics_final_vibe

        # Update audio vibe for each track, doesn't matter if it was already in the database
        track_vibe.track_audio_vibe = deduce_audio_vibe([audio_features_list[index]])

        track_vibe.save()

    return audio_final_vibe, lyrics_final_vibe


def deduce_lyrics(track_names, track_artists, track_ids):
    genius = lyricsgenius.Genius(os.getenv("GENIUS_CLIENT_ACCESS_TOKEN"))
    genius.timeout = 15

    lyrics_vibes = []

    lyrics_data = {}
    for track, artist, id in zip(track_names, track_artists, track_ids):
        genius_retries = 0
        while genius_retries < 2:
            try:
                query = f'"{track}" "{artist}"'
                song = genius.search_song(query)

            except Exception as e:
                retries += 1
                continue

            if song is not None:
                # Genius song object sometimes has trailing space, so need to strip
                geniusTitle = song.title.lower().replace("\u200b", " ").strip()
                geniusArtist = song.artist.lower().replace("\u200b", " ").strip()
                if geniusTitle == track.lower() and geniusArtist == artist.lower():
                    print("Inputting lyrics..")
                    lyrics_data[(track, artist, id)] = song.lyrics
            
            break


    openai.api_key = os.getenv("OPEN_AI_TOKEN")

    for (track, artist, id), lyrics in lyrics_data.items():
        short_lyrics = lyrics[:2048]
        retries = 0
        while retries < MAX_RETRIES:
            try:
                print(f"Processing song. Track: {track}, Artist: {artist}, ID: {id}")
                print(f"Lyrics: {short_lyrics[:200]}")
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful assistant."},
                        {
                            "role": "user",
                            "content": f"You are a mood analyzer that can only return a single word. Based on these song lyrics, return a single word that matches this song's mood: '{short_lyrics}'",
                        },
                    ],
                    request_timeout=5,
                )
                vibe = response.choices[0].message["content"].strip()
                checkLength = vibe.split()
                if len(checkLength) == 1:
                    lyrics_vibes.append(vibe.lower())

                    # INSERT VIBE HERE INTO TRACK DATABASE!!!!!
                print(f"The vibe for {track} is: {vibe}")

                break
            except Exception as e:
                print(f"Error processing the vibe for {track}: {e}")
                retries += 1

            if retries >= MAX_RETRIES:
                print(f"Retries maxed out processing the vibe for {track}.")
                break
            else:
                time.sleep(1)

    return lyrics_vibes


def lyrics_vectorize(lyrics_vibes):
    if lyrics_vibes:
        for i in lyrics_vibes:
            print("Lyrics vibes: " + i)
        avg_lyr_vibe = average_vector(lyrics_vibes)
        closest_emotion = find_closest_emotion(avg_lyr_vibe)
        return str(closest_emotion)
    else:
        return None


def average_vector(words):
    # Compute the average vector for a list of words.
    vectors = []
    for word in words:
        try:
            str_vector = client.predict("get_vector", word, api_name="/predict")
            vector = string_to_vector(str_vector)
            vectors.append(vector)
        except Exception as e:
            print(f"Error processing word '{word}': {e}")

    if vectors:
        return np.mean(vectors, axis=0)
    else:
        # Return a zeros vector of 300 dimension
        return np.zeros(300)


def string_to_vector(str):
    clean = re.sub(r"[\[\]\n\t]", "", str)
    clean = clean.split()
    clean = [float(e) for e in clean]
    return clean


def find_closest_emotion(final_vibe):
    emotion_words = [
        "happy",
        "sad",
        "angry",
        "anxious",
        "content",
        "excited",
        "bored",
        "nostalgic",
        "frustrated",
        "hopeful",
        "afraid",
        "confident",
        "jealous",
        "grateful",
        "lonely",
        "rebellious",
        "relaxed",
        "amused",
        "curious",
        "ashamed",
        "sympathetic",
        "disappointed",
        "proud",
        "enthusiastic",
        "empathetic",
        "shocked",
        "calm",
        "inspired",
        "indifferent",
        "romantic",
        "tense",
        "euphoric",
        "restless",
        "serene",
        "sensual",
        "reflective",
        "playful",
        "dark",
        "optimistic",
        "mysterious",
        "seductive",
        "regretful",
        "detached",
        "melancholic",
    ]

    max_similarity = -1
    closest_emotion = None
    for word in emotion_words:
        word_vec = get_emotion_vector(word)
        similarity = cosine_similarity(final_vibe, word_vec)
        if similarity > max_similarity:
            max_similarity = similarity
            closest_emotion = word
    return closest_emotion


def get_emotion_vector(input_emotion):
    input_emotion = input_emotion.lower()
    vector_str = EmotionVector.objects.filter(emotion=input_emotion).first()

    if not vector_str:
        # We should always get vector string stored in our database,
        # but if somehow is not in database..
        vector_str = client.predict("get_vector", input_emotion, api_name="/predict")
    else:
        vector_str = vector_str.vector

    return string_to_vector(vector_str)


def cosine_similarity(vec_a, vec_b):
    return np.dot(vec_a, vec_b) / (np.linalg.norm(vec_a) * np.linalg.norm(vec_b))


def vibe_description(final_vibe):
    openai.api_key = os.getenv("OPEN_AI_TOKEN")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {
                    "role": "user",
                    "content": f"This is the output of a program that takes listening history of a person (spotify "
                    f"features) and their lyrics and classifies a daily final vibe. Take the daily final vibe, "
                    f"this being: '{final_vibe}', and briefly describe today's person music vibe and energy as "
                    f"if you were talking to them. Use pop culture terms, artists as references as be brief "
                    f"but precise.",
                },
            ],
            request_timeout=50,
        )

        response = response.choices[0].message["content"].strip()
        return response

    except Exception:
        return None


def get_feature_average(list, feature):
    total = sum(track[feature] for track in list)
    average = total / len(list)
    return average
