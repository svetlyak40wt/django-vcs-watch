import calendar
import datetime
import pytz

from django.conf.urls.defaults import *
from django.utils.translation import ugettext_lazy as _
from django_vcs_watch.models import Repository, Commit, FeedItem
from django_vcs_watch.forms import RepositoryForm
from django_vcs_watch.feeds import LatestRepositories, LatestCommits

from django_globals import globals

def timestamp():
    return calendar.timegm(pytz.utc.localize(datetime.datetime.utcnow()).timetuple())

def get_tb(request):
    if 'tb' in request.GET:
        return pytz.utc.localize(
            datetime.datetime.utcfromtimestamp(
                int(request.GET.get('tb'))))
    return pytz.utc.localize(datetime.datetime.utcnow())


repository_detail = {
    'cls': Repository,
    'query': lambda request, slug: {
        'slug': slug,
    },
    'template_name': 'django_vcs_watch/repository_detail.html',
}

user_commits_dict = dict(
    extra_context = dict(title = _('User commits')),
    template = 'django_vcs_watch/user_commits.html',
)

feed_items = {
    'cls': FeedItem,
    'query': lambda request, slug: {
        'slug': slug,
        'date' : {'$lt': get_tb(request)}
    },
    'paginate_by': 20,
    'template_name': 'django_vcs_watch/repository_detail.html',
    'template_object_name': 'commits_list',
    'map_func': lambda x: x.commit,
}

feeds = {
    'commits': LatestCommits,
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

create_repository_page = {
    'form_class': RepositoryForm,
    'template_name': 'django_vcs_watch/create_repository.html',
    'extra_context': { 'user': lambda: globals.user },
}

urlpatterns = patterns('django_vcs_watch.views',
   (r'^r/feed/$',
        'feed', {'slug': 'repositories', 'feed_dict': feeds}, 'vcs-watch-feed-repositories'),
   (r'^r/(?P<param>[a-z0-9-]+)/feed/$',
        'feed', {'slug': 'commits', 'feed_dict': feeds}, 'vcs-watch-feed-commits'),
   (r'^r/(?P<repository_slug>[a-z0-9-]+)/(?P<revision>[a-z0-9-]{1,36})/$',
        'commit', {}, 'vcs-watch-commit'),
   (r'^profile/$', 'profile', {}, 'vcs-watch-profile'),
   (r'^autocomplete/$', 'autocomplete', autocomplete, 'vcs-watch-autocomplete'),
   (r'^add/$', 'create', create_repository_page, 'vcs-watch-add'),
   (r'^r/(?P<slug>[a-z0-9-]+)/$',
        'object_detail', repository_detail, 'vcs-watch-repository'),
   (r'^f/(?P<slug>[a-z0-9-]+)/$',
        'object_list', feed_items, 'vcs-watch-feed'),
   (r'^refresh-feed/$',
        'refresh_feed', {}, 'vcs-watch-refresh-feed'),
   (r'^ignore/$', 'ignore', {}, 'vcs-watch-ignore'),
   (r'^unignore/$', 'unignore', {}, 'vcs-watch-unignore'),
   (r'^watch/$', 'watch', {}, 'vcs-watch-watch'),
   (r'^unwatch/$', 'unwatch', {}, 'vcs-watch-ununwatch'),
)

urlpatterns += patterns('django.views.generic',
   (r'^r/$', 'simple.direct_to_template', main_page, 'vcs-watch-repositories'),
   (r'^u/(?P<author>.*)/$', 'simple.direct_to_template', user_commits_dict, 'vcs-watch-commits-by'),
)

