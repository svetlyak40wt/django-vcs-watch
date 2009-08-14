from django.conf.urls.defaults import *
from models import Repository, Revision
from forms import RepositoryForm
from feeds import LatestRevisions, LatestRepositories

from django_globals import globals

repository_info = {
    'queryset': Repository.objects.all(),
    'slug_field': 'slug'
}

revision_info = {
    'queryset': Revision.objects.all(),
    'slug_field': 'slug'
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

autocomplete = {
    'template_name': 'django_vcs_watch/autocomplete.html'
}

add_page = {
    'form_class': RepositoryForm,
    'extra_context': { 'user': lambda: globals.user },
}

urlpatterns = patterns('django.views.generic',
   (r'^r/(?P<slug>[a-z0-9-]+)/$',
        'list_detail.object_detail', repository_info, 'vcs-watch-repository'),
   (r'^add/$', 'create_update.create_object', add_page, 'vcs-watch-add'),
   #(r'^r/$', 'simple.direct_to_template', main_page, 'vcs-watch-main-page'),
)

urlpatterns += patterns('django_vcs_watch.views',
   (r'^r/(?P<repository_slug>[a-z0-9-]+)/(?P<revision>[a-z0-9-]{1,36})/$', 'revision', {}, 'vcs-watch-revision'),
   (r'^profile/$', 'profile', {}, 'vcs-watch-profile'),
   (r'^autocomplete/$', 'autocomplete', autocomplete, 'vcs-watch-autocomplete'),
)

urlpatterns += patterns('django.contrib.syndication.views',
   (r'^feed/(?P<url>.*)/$', 'feed', {'feed_dict': feeds}, 'vcs-watch-feeds'),
)

