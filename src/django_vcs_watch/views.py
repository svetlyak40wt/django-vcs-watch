from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_detail, object_list
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from models import Repository

def revision(request, repository_hash, revision):
    repository = get_object_or_404(Repository, hash=repository_hash)
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

