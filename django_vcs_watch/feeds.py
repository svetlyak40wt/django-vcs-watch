from django.contrib.syndication.feeds import FeedDoesNotExist, Feed
from django.core.exceptions import ObjectDoesNotExist
from models import Repository

class LatestRepositories(Feed):
    title = 'Latest repositories'
    link = '/vcs/'
    description = 'Latest VCS repositories'

    def items(self):
        return Repository.objects.filter(public=True)[:20]


class LatestRevisions(Feed):
    def get_object(self, bits):
        if len(bits) != 1:
            raise ObjectDoesNotExist
        return Repository.objects.get(hash__exact=bits[0])

    def title(self, obj):
        return 'Changes at %s' % obj.url

    def link(self, obj):
        if not obj:
            raise FeedDoesNotExist
        return obj.get_absolute_url()

    def description(self, obj):
        return 'Latest changes at %s' % obj.url

    def items(self, obj):
        return obj.revision_set.all()

    def item_pubdate(self, item):
        return item.date

