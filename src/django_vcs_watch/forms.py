from django import forms
from models import Repository
from django_vcs_watch.settings import VCS_ONLY_PUBLIC_REPS, \
                                      VCS_URL_REWRITER

class _BaseForm(forms.ModelForm):
    def clean_url(self):
        return VCS_URL_REWRITER(self.cleaned_data['url'])

class PrivateRepositoryForm(_BaseForm):
    password = forms.CharField(
            max_length=Repository._meta.get_field('password').max_length,
            required=(not Repository._meta.get_field('password').blank),
            widget=forms.PasswordInput())

    class Meta:
        model = Repository

class PublicRepositoryForm(_BaseForm):
    class Meta:
        model = Repository
        fields = ('url', )

if VCS_ONLY_PUBLIC_REPS:
    RepositoryForm = PublicRepositoryForm
else:
    RepositoryForm = PrivateRepositoryForm

