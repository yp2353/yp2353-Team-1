from django import forms


class UsersearchForm(forms.Form):
    username = forms.CharField(max_length=250, required=True, label="username")


class FriendshipRequestForm(forms.Form):
    username = forms.CharField(max_length=250, required=True)
