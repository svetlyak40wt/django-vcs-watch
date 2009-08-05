from django import forms
from models import Repository
from django.conf import settings

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

PUBLIC = getattr(settings, 'VCS_ONLY_PUBLIC_REPS', False)

if PUBLIC:
    RepositoryForm = PublicRepositoryForm
else:
    RepositoryForm = PrivateRepositoryForm

