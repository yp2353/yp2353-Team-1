from django import forms


class SearchForm(forms.Form):
    search_query = forms.CharField(label="Track", max_length=100)
