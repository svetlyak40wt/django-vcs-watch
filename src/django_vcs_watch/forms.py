from django import forms
from models import Repository
from django_vcs_watch.settings import *

class PrivateRepositoryForm(forms.ModelForm):
    password = forms.CharField(
            max_length=Repository._meta.get_field('password').max_length,
            required=(not Repository._meta.get_field('password').blank),
            widget=forms.PasswordInput())

    class Meta:
        model = Repository

class PublicRepositoryForm(forms.ModelForm):
    class Meta:
        model = Repository
        fields = ('url', )

if VCS_ONLY_PUBLIC_REPS:
    RepositoryForm = PublicRepositoryForm
else:
    RepositoryForm = PrivateRepositoryForm

