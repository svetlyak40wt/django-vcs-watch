from django import forms
from models import Repository

class RepositoryForm(forms.ModelForm):
    password = forms.CharField(
            max_length=Repository._meta.get_field('password').max_length,
            required=(not Repository._meta.get_field('password').blank),
            widget=forms.PasswordInput())

    class Meta:
        model = Repository

