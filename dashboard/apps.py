from django.apps import AppConfig
import joblib
import sys


class DashboardConfig(AppConfig):
    name = "dashboard"
    model = None  # Initialize the model attribute

    def ready(self):
        if not self.model:
            if sys.version_info.minor >= 11:
                audio_model_path = "assets/Gradient_Boosting_Classifier_3.11.bin"
                self.model = joblib.load(audio_model_path)
            else:
                # If Python version lower than 3.7, raise an error
                raise RuntimeError("Python version lower than 3.7 is not supported")
