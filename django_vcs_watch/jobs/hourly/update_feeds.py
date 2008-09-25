from django_extensions.management.jobs import HourlyJob

from django_vcs_watch.models import Repository

class Job(HourlyJob):
    help = "Update VCS feeds"

    def execute(self):
        for repos in Repository.objects.all():
            repos.updateFeed()
