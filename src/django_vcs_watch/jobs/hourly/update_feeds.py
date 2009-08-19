import os
import logging
import time
from datetime import datetime

from django.conf import settings
from django.db.models import Q

from django_extensions.management.jobs import HourlyJob
from django_vcs_watch.models import Repository
from django_vcs_watch.settings import DELAY_BETWEEN_UPDATE_CHECK

class Job(HourlyJob):
    help = "Update VCS feeds"

    def execute(self):
        log = logging.getLogger('django_vcs_watch.jobs.update_feeds')

        pidfile = getattr(settings, 'VCS_WATCH_PID_FILE', '/tmp/vcswatch_update_feeds.pid')

        if os.path.exists(pidfile):
            pid = int(open(pidfile).read())
            if os.path.exists('/proc/%d' % pid):
                log.warning('Job already running with pid %d (pidfile "%s" exists)' % (pid, pidfile))
                return

        f = open(pidfile, 'w')
        try:
            f.write(str(os.getpid()))
        finally:
            f.close()

        try:
            while True:
                self.update_repositories()
                time.sleep(DELAY_BETWEEN_UPDATE_CHECK)
        finally:
            os.remove(pidfile)


    def update_repositories(self):
        log = logging.getLogger('django_vcs_watch.jobs.update_feeds')
        reps_to_update = Repository.objects.filter(
                Q(next_check_at__isnull = True) |
                Q(next_check_at__lte = datetime.utcnow()))

        for rep in reps_to_update:
            log.debug('rep to update: %s' % rep.url)

        for rep in reps_to_update:
            try:
                rep.updateFeed()
            except Exception, e:
                log.exception("can't update feed for rep %s" % rep)

