from django.conf.urls.defaults import *
from models import Repository

info_dict = {
    'queryset': Repository.objects.all(),
    'slug_field': 'hash'
}

urlpatterns = patterns('django.views.generic',
   (r'^(?P<slug>[a-z0-9]{8}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{4}-[a-z0-9]{12})/$', 'list_detail.object_detail', info_dict),
)

