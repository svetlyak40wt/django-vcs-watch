from django import template
from django_vcs_watch.models import Revision

register = template.Library()

@register.inclusion_tag('django_vcs_watch/commits_list.html')
def latest_commits():
    return {
        'commits': Revision.objects.all()[:10],
    }
