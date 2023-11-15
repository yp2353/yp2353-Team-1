from django import forms


class SearchRoomFrom(forms.Form):
    search_query = forms.CharField(label="Search Room", max_length=100)
