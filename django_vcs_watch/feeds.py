from django.contrib.syndication.feeds import FeedDoesNotExist, Feed
from django.core.exceptions import ObjectDoesNotExist
from models import Repository
from django.utils.translation import ugettext_lazy as _

class LatestRepositories(Feed):
    title = _('Last updated repositories')
    # TODO reverse
    link = '/vcs/'
    description = _('Last updated VCS repositories')

    def items(self):
        return Repository.objects.filter(public=True)[:20]

    def item_pubdate(self, item):
        return item.updated_at


class LatestRevisions(Feed):
    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Repository.objects.get(hash__exact=bits[0])

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

