from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_detail, object_list
from django.views.generic.create_update import create_object
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, HttpResponseRedirect

from django_vcs_watch.models import Repository

def revision(request, repository_slug, revision):
    repository = get_object_or_404(Repository, slug=repository_slug)
    return object_detail(
            request,
            queryset=repository.revision_set.all(),
            slug=revision,
            slug_field='rev')


@login_required
def profile(request):
    return object_list(
            request,
            queryset=request.user.repository_set.all())

