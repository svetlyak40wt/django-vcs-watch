import os
import logging

from django_extensions.management.jobs import HourlyJob
from django_vcs_watch.models import Repository
from django.conf import settings

class Job(HourlyJob):
    help = "Update VCS feeds"

    def execute(self):
        _log = logging.getLogger('django_vcs_watch.jobs.update_feeds')

        pidfile = getattr(settings, 'VCS_WATCH_PID_FILE', '/tmp/vcswatch_update_feeds.pid')

        if os.path.exists(pidfile):
            pid = int(open(pidfile).read())
            if os.path.exists('/proc/%d' % pid):
                _log.warning('Job already running with pid %d (pidfile "%s" exists)' % (pid, pidfile))
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
                _log.exception("can't update feed for repo %s" % repos)

        os.remove(pidfile)

