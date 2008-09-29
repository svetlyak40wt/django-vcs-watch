from django.conf.urls.defaults import *
from models import Repository
from forms import RepositoryForm
from feeds import LatestRevisions, LatestRepositories

info_dict = {
    'queryset': Repository.objects.all(),
    'slug_field': 'hash'
}

feeds = {
    'diffs': LatestRevisions,
    'repositories': LatestRepositories,
}

main_page = {
    'template': 'django_vcs_watch/main.html',
    'extra_context': {
        'repositories': lambda: Repository.objects.filter(public=True)[:10],
    }
}

add_page = {
    'form_class': RepositoryForm,
}

urlpatterns = patterns('django.views.generic',
   (r'^(?P<slug>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})/$', 'list_detail.object_detail', info_dict),
   (r'^add/$', 'create_update.create_object', add_page),
   (r'^$', 'simple.direct_to_template', main_page),
)

urlpatterns += patterns('django.contrib.syndication.views',
   (r'^feed/(?P<url>.*)/$', 'feed', {'feed_dict': feeds}, 'vcs-watch-feeds'),
)

