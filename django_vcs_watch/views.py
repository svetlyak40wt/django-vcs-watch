from django.shortcuts import get_object_or_404
from django.views.generic.list_detail import object_detail

from models import Repository

def revision(request, repository_hash, revision):
    repository = get_object_or_404(Repository, hash=repository_hash)
    return object_detail(
            request,
            queryset=repository.revision_set.all(),
            slug=revision,
            slug_field='rev')

