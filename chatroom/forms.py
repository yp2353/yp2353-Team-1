from django import forms
from .models import ChatMessage


class UserMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ["user", "message"]
