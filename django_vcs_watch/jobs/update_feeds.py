from django_extensions.management.jobs import BaseJob

from django_vcs_watch.models import Repository

class Job(BaseJob):
    help = "Update VCS feeds"

    def execute(self):
        for repos in Repository.objects.all():
            repos.updateFeed()
