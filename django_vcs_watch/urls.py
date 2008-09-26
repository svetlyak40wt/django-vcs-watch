from django.conf.urls.defaults import *
from models import Repository
from feeds import LatestRevisions, LatestRepositories

info_dict = {
    'queryset': Repository.objects.all(),
    'slug_field': 'hash'
}

feeds = {
    'diffs': LatestRevisions,
    'repositories': LatestRepositories,
}

urlpatterns = patterns('django.views.generic',
   (r'^(?P<slug>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})/$', 'list_detail.object_detail', info_dict),
)

urlpatterns += patterns('django.contrib.syndication.views',
   (r'^feed/(?P<url>.*)/$', 'feed', {'feed_dict': feeds}),
)

