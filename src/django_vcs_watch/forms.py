import uuid
from django import forms
from django.utils.translation import ugettext_lazy as _

from django_vcs_watch.models import Repository
from django_vcs_watch.settings import VCS_ONLY_PUBLIC_REPS, \
                                      VCS_URL_REWRITER
from django_vcs_watch.utils import make_slugs

class _BaseForm(forms.ModelForm):
    def clean_url(self):
        return VCS_URL_REWRITER(self.cleaned_data['url'])

    def clean_slug(self):
        url = self.clean_url()

        if len(Repository.objects.filter(url=url)) == 0:
            def slug_exists(slug):
                return len(Repository.objects.filter(slug=slug)) > 0

            slug = self.cleaned_data['slug']
            if slug:
                if slug_exists(slug):
                    raise forms.ValidationError(_('Repository with slug "%s" already exists.') % slug)
                return slug

            slugs = make_slugs(url)
            for slug in slugs:
                if not slug_exists(slug):
                    return slug
            raise forms.ValidationError(_('Please, specify slug for this URL.'))

    def save(self):
        try:
            return Repository.objects.get(url=self.cleaned_data['url'])
        except Repository.DoesNotExist:
            pass
        return super(_BaseForm, self).save()


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
        fields = ('url', 'slug')

if VCS_ONLY_PUBLIC_REPS:
    RepositoryForm = PublicRepositoryForm
else:
    RepositoryForm = PrivateRepositoryForm

