from django.apps import AppConfig
import joblib

class DashboardConfig(AppConfig):
    name = "dashboard"
    model = None  # Initialize the model attribute

    def ready(self):
        if not self.model:
            self.model = joblib.load('assets/Gradient_Boosting_Classifier.bin')