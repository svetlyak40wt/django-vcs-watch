from django.contrib.syndication.feeds import FeedDoesNotExist, Feed
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat

from django_vcs_watch.models import Repository

class LatestRepositories(Feed):
    title = _('Last added repositories')
    description = _('Last added VCS repositories')

    def link(self):
        return reverse('vcs-watch-repositories')

    def items(self):
        return Repository.objects.filter(public=True).exclude(updated_at=None).order_by('-created_at')[:20]

    def item_pubdate(self, item):
        return item.created_at


class LatestCommits(Feed):
    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        repository = Repository.objects.get(slug__exact=bits[0])
        repository.update_last_access()
        return repository

    def description(self, obj):
        if obj.last_error is not None:
            return string_concat(
                '<b>',
                _('We encounter an error during downloading diffs from this repository:'),
                '</b><br />',
                obj.last_error)

    def title(self, obj):
        return _('Latest changes at %s') % obj.url

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def items(self, obj):
        return obj.revision_set.all()

    def item_pubdate(self, item):
        return item.date

    def item_author_name(self, item):
        return item.author

