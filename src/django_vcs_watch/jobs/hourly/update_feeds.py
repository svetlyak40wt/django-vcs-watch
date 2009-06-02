import os
import logging

from django_extensions.management.jobs import HourlyJob
from django_vcs_watch.models import Repository
from django.conf import settings

class Job(HourlyJob):
    help = "Update VCS feeds"

    def execute(self):
        _log = logging.getLogger('django_vcs_watch.jobs.update_feeds')

        pidfile = os.path.join(getattr(settings, 'VCS_WATCH_PID_DIR', '/tmp'), 'vcswatch_update_feeds.pid')
        if os.path.exists(pidfile):
            pid = int(open(pidfile).read())
            if os.path.exists('/proc/%d' % pid):
                _log.warning('Job already running with pid %d' % pid)
                return

        f = open(pidfile, 'w')
        try:
            f.write(str(os.getpid()))
        finally:
            f.close()

        for repos in Repository.objects.all():
            try:
                repos.updateFeed()
            except Exception, e:
                _log.error(e)

        os.remove(pidfile)

