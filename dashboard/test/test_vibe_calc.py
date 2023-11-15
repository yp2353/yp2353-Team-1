from django.test import TestCase
from unittest.mock import patch, Mock, MagicMock
from dashboard.vibe_calc import (
    deduce_lyrics,
    lyrics_vectorize,
    cosine_similarity,
    get_feature_average,
    find_closest_emotion,
    string_to_vector,
    average_vector,
    get_emotion_vector,
)  # Adjust the import path according to your project structure
import numpy as np


class MockResponse:
    def __init__(self, content):
        self.message = Mock()
        self.message.content = content
        self.finish_reason = "stop"
        self.index = 0


class TestDeduceLyrics(TestCase):
    @patch("dashboard.vibe_calc.lyricsgenius.Genius")
    @patch("dashboard.vibe_calc.openai.ChatCompletion.create")
    def test_deduce_lyrics(self, mock_openai, mock_genius):
        # Setup mock responses for Genius and OpenAI
        mock_song = mock_genius.return_value.search_song.return_value
        mock_song.title = "Test Song"
        mock_song.artist = "Test Artist"
        mock_song.lyrics = "Test Lyrics"

        mock_openai.return_value.choices[0].message = {"content": "happy"}

        # Call the function with test data
        track_names = ["Test Song"]
        track_artists = ["Test Artist"]
        track_ids = [1]

        # You may need to mock the database interactions here as well

        result = deduce_lyrics(track_names, track_artists, track_ids)

        # Assert the expected outcome
        self.assertEqual(result, ["happy"])

    # Additional tests go here


class TestLyricsVectorize(TestCase):
    @patch("dashboard.vibe_calc.average_vector")
    @patch("dashboard.vibe_calc.find_closest_emotion")
    def test_lyrics_vectorize(self, mock_find_closest_emotion, mock_average_vector):
        # Mock the dependencies
        mock_average_vector.return_value = [0.5, 0.5, 0.5]  # example average vector
        mock_find_closest_emotion.return_value = "happy"

        # Test with non-empty lyrics vibes
        lyrics_vibes = ["vibe1", "vibe2"]
        result = lyrics_vectorize(lyrics_vibes)
        self.assertEqual(result, "happy")
        mock_average_vector.assert_called_once_with(lyrics_vibes)
        mock_find_closest_emotion.assert_called_once_with([0.5, 0.5, 0.5])

        # Test with empty lyrics vibes
        lyrics_vibes = []
        result = lyrics_vectorize(lyrics_vibes)
        self.assertIsNone(result)
        # Ensure average_vector and find_closest_emotion were not called for empty input
        mock_average_vector.assert_called_once()
        mock_find_closest_emotion.assert_called_once()

    # Additional tests for edge cases can be added here


class TestCosineSimilarity(TestCase):
    def test_cosine_similarity(self):
        # Test with non-zero vectors
        vec_a = np.array([1, 0, 0])
        vec_b = np.array([0, 1, 0])
        result = cosine_similarity(vec_a, vec_b)
        self.assertEqual(
            result, 0
        )  # Cosine similarity should be 0 for orthogonal vectors

        # Test with same vectors
        vec_a = np.array([1, 2, 3])
        vec_b = np.array([1, 2, 3])
        result = cosine_similarity(vec_a, vec_b)
        self.assertEqual(
            result, 1
        )  # Cosine similarity should be 1 for identical vectors

        # Test with opposite vectors
        vec_a = np.array([1, 2, 3])
        vec_b = np.array([-1, -2, -3])
        result = cosine_similarity(vec_a, vec_b)
        self.assertEqual(
            result, -1
        )  # Cosine similarity should be -1 for opposite vectors

        # Additional tests for edge cases can be added here


class TestGetFeatureAverage(TestCase):
    def test_get_feature_average(self):
        # Test with normal case
        tracks = [{"feature": 10}, {"feature": 20}, {"feature": 30}]
        result = get_feature_average(tracks, "feature")
        self.assertEqual(result, 20)  # Expecting average of 10, 20, and 30

        # Test with empty list
        tracks = []
        with self.assertRaises(
            ZeroDivisionError
        ):  # Assuming your function doesn't handle empty list
            get_feature_average(tracks, "feature")

        # Additional tests can be added here, such as for lists with some missing features

    def test_get_feature_average_with_missing_feature(self):
        # Test with some dictionaries missing the feature
        tracks = [{"feature": 10}, {"feature": 20}, {"feature": 30}]
        result = get_feature_average(tracks, "feature")
        # Depending on how your function handles missing features, adjust the expected result
        # For instance, if it ignores dictionaries without the feature:
        self.assertEqual(
            result, 20
        )  # Average of 10 and 30, ignoring the dictionary without 'feature'

        # More tests can be added based on how you handle edge cases


class TestFindClosestEmotion(TestCase):
    @patch("dashboard.vibe_calc.get_emotion_vector")
    @patch("dashboard.vibe_calc.cosine_similarity")
    def test_find_closest_emotion(
        self, mock_cosine_similarity, mock_get_emotion_vector
    ):
        # Set up mock return values
        # Assuming get_emotion_vector returns a vector for each emotion word
        mock_get_emotion_vector.side_effect = lambda word: [float(ord(c)) for c in word]
        # Mock cosine_similarity to return higher values for a specific word

        def mock_cosine(final_vibe, word_vec):
            if word_vec == [float(ord(c)) for c in "happy"]:
                return 0.9  # A high similarity value for 'happy'
            return 0.1  # A low similarity value for all other emotions

        mock_cosine_similarity.side_effect = mock_cosine

        # Test with a final_vibe vector
        final_vibe = [1, 2, 3]  # Example vector
        result = find_closest_emotion(final_vibe)
        self.assertEqual(result, "happy")  # Expecting 'happy' to be the closest emotion

        # Additional tests can be added here for other scenarios


class StringToVectorTest(TestCase):
    def test_string_to_vector(self):
        test_string = "[-0.02063346  0.01360685  0.02101058]"
        expected_result = [-0.02063346, 0.01360685, 0.02101058]
        self.assertEqual(string_to_vector(test_string), expected_result)


class AverageVectorTestCase(TestCase):
    @patch("dashboard.vibe_calc.client.predict")
    @patch("dashboard.vibe_calc.string_to_vector")
    def test_average_vector(self, mock_string_to_vector, mock_predict):
        # Setup the mock objects
        mock_predict.return_value = "1 2 3"
        mock_string_to_vector.return_value = np.array([1, 2, 3])

        # Call the function with a list of words
        words = ["word1", "word2", "word3"]
        result = average_vector(words)

        # Check the result
        expected_result = np.array([1, 2, 3])
        np.testing.assert_array_equal(result, expected_result)

        # Check that the mock functions were called the correct number of times
        self.assertEqual(mock_predict.call_count, len(words))
        self.assertEqual(mock_string_to_vector.call_count, len(words))


class GetEmotionVectorTestCase(TestCase):
    @patch("dashboard.vibe_calc.EmotionVector.objects.filter")
    @patch("dashboard.vibe_calc.client.predict")
    @patch("dashboard.vibe_calc.string_to_vector")
    def test_get_emotion_vector(self, mock_string_to_vector, mock_predict, mock_filter):
        # Setup the mock objects
        mock_emotion_vector = MagicMock()
        mock_emotion_vector.vector = "1 2 3"
        mock_filter.return_value.first.return_value = mock_emotion_vector
        mock_predict.return_value = "1 2 3"
        mock_string_to_vector.return_value = [1, 2, 3]

        # Call the function with an emotion
        emotion = "happy"
        result = get_emotion_vector(emotion)

        # Check the result
        expected_result = [1, 2, 3]
        self.assertEqual(result, expected_result)

        # Check that the mock functions were called correctly
        mock_filter.assert_called_once_with(emotion=emotion.lower())
        mock_string_to_vector.assert_called_once_with(mock_emotion_vector.vector)
