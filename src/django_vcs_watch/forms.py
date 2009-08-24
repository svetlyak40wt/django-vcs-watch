import uuid
from pdb import set_trace

from django import forms
from django.utils.translation import ugettext_lazy as _

from django_vcs_watch.models import Repository
from django_vcs_watch.settings import VCS_ONLY_PUBLIC_REPS, \
                                      VCS_URL_REWRITER
from django_vcs_watch.utils import make_slug



def find_unused_slug(slug):
    def slug_exists(slug):
        return len(Repository.objects.find({'slug': slug})) > 0

    if not slug_exists(slug):
        return slug

    for i in xrange(2, 1000):
        new_slug = '%s-%d' % (slug, i)
        if not slug_exists(new_slug):
            return new_slug
    raise Exception("Can't find unused slug.")



class RepositoryForm(forms.Form):
    url      = forms.CharField(max_length = 255)
    slug     = forms.SlugField(required = False)
    username = forms.CharField(max_length = 40, required = False)
    password = forms.CharField(max_length = 40, required = False, widget = forms.PasswordInput())

    def clean_url(self):
        return VCS_URL_REWRITER(self.cleaned_data.get('url', ''))

    def save(self):
        repository = Repository.objects.find_one({'url': self.cleaned_data['url']})

        data = {
            'public': True,
            'slug': None,
        }
        data.update(self.cleaned_data)

        if repository:
            if not data['slug']:
                del data['slug']
            repository.update(data)
        else:
            slug = data['slug']
            if not slug:
                slug = make_slug(data['url'])

            real_slug = find_unused_slug(slug)
            if data['slug'] != real_slug:
                data['original_slug'] = data['slug']
                data['slug'] = real_slug

            repository = Repository(**data)

        return repository.save()

