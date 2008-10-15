import os
import logging

from django_extensions.management.jobs import BaseJob
from django_vcs_watch.models import Repository
from django.conf import settings

class Job(BaseJob):
    help = "Update VCS feeds"

    def execute(self):
        pidfile = os.path.join(getattr(settings, 'PID_DIR', '/tmp'), 'vcswatch_update_feeds.pid')
        if os.path.exists(pidfile):
            pid = int(open(pidfile).read())
            if os.path.exists('/proc/%d' % pid):
                _log = logging.getLogger('django_vcs_watch.jobs.update_feeds')
                _log.warning('Job already running with pid %d' % pid)
                return

        f = open(pidfile, 'w')
        try:
            f.write(str(os.getpid()))
        finally:
            f.close()

        for repos in Repository.objects.all():
            repos.updateFeed()

        os.remove(pidfile)
