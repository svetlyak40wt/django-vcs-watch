import os
import logging
import time
import datetime

from itertools import chain
from django.conf import settings

from django_extensions.management.jobs import HourlyJob
from django_vcs_watch.models import Repository, Commit
from django_vcs_watch.settings import DELAY_BETWEEN_UPDATE_CHECK
from django_vcs_watch.utils import mongo

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
        db = mongo()

        new_reps = Repository.objects.find({'next_check_at': None})
        reps_to_update = Repository.objects.find({'next_check_at': {'$lte': datetime.datetime.utcnow()}})

        for rep in chain(new_reps, reps_to_update):
            log.debug('rep to update: %s' % rep.url)
            try:
                rep.updateFeed()
            except Exception, e:
                log.exception("can't update feed for rep %s" % rep)

        Commit.objects.ensure_index([('date', 1)])

