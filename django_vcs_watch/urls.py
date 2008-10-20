from django.conf.urls.defaults import *
from models import Repository, Revision
from forms import RepositoryForm
from feeds import LatestRevisions, LatestRepositories

from django_globals import globals

repository_info = {
    'queryset': Repository.objects.all(),
    'slug_field': 'hash'
}

revision_info = {
    'queryset': Revision.objects.all(),
    'slug_field': 'hash'
}

feeds = {
    'diffs': LatestRevisions,
    'repositories': LatestRepositories,
}

main_page = {
    'template': 'django_vcs_watch/main.html',
    'extra_context': {
        'repositories': lambda: Repository.objects.filter(public=True).exclude(updated_at=None)[:10],
    }
}

add_page = {
    'form_class': RepositoryForm,
    'extra_context': { 'user': lambda: globals.user },
}

urlpatterns = patterns('django.views.generic',
   (r'^(?P<slug>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})/$', 'list_detail.object_detail', repository_info, 'vcs-watch-repository'),
   (r'^add/$', 'create_update.create_object', add_page, 'vcs-watch-add'),
   (r'^$', 'simple.direct_to_template', main_page, 'vcs-watch-main-page'),
)

urlpatterns += patterns('django_vcs_watch.views',
   (r'^(?P<repository_hash>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})/(?P<revision>[a-z0-9-]{1,36})/$', 'revision', {}, 'vcs-watch-revision'),
   (r'^profile/$', 'profile', {}, 'vcs-watch-profile'),
)

urlpatterns += patterns('django.contrib.syndication.views',
   (r'^feed/(?P<url>.*)/$', 'feed', {'feed_dict': feeds}, 'vcs-watch-feeds'),
)

