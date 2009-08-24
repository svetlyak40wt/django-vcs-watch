import calendar
import datetime
import logging
import operator
import os
import pytz

from pdb import set_trace

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import DjangoUnicodeDecodeError

from django_fields.fields import EncryptedCharField

from django_vcs_watch.settings import \
    REVISION_LIMIT, \
    CHECK_INTERVAL_MIN, \
    CHECK_INTERVAL_MAX

from django_vcs_watch.utils import \
    timedelta_to_string, \
    strip_timezone, \
    mongo

from pymongo import DESCENDING
from mongobongo import Document


if 'django_globals' not in settings.INSTALLED_APPS:
    raise Exception('Please, install django_globals application.')

if 'django_globals.middleware.User' not in settings.MIDDLEWARE_CLASSES:
    raise Exception('Please, add django_globals.middleware.User to the MIDDLEWARE_CLASSES.')


def delta2secs(d):
    return d.days * 24 * 60 * 60 + d.seconds


class Commit(Document):
    collection = 'commits'

    class Meta:
        ordering = [('date', DESCENDING)]

    def __unicode__(self):
        return _('Commit %(revision)s by %(author)s') % self.__dict__

    @models.permalink
    def get_absolute_url(self):
        return ('vcs-watch-commit', (), {'repository_slug': self.slug, 'revision': self.revision})

    def get_timestamp(self):
        if self.date is not None:
            return calendar.timegm(self.utcdate.timetuple())
        return 0

    @property
    def utcdate(self):
        return pytz.utc.localize(self._data.get('date'))



class Repository(Document):
    collection = 'repositories'

    def __unicode__(self):
        return _('Repository at %s') % self.url


    @models.permalink
    def get_absolute_url(self):
        return ('vcs-watch-repository', (), {'slug': self.slug})


    @models.permalink
    def get_rss_url(self):
        return ('vcs-watch-feed-commits', (), {'param': self.slug })


    def updateFeed(self):
        log = logging.getLogger('django_vcs_watch.repository.updateFeed')
        log.debug('update %s' % self.slug)

        from django_vcs_watch.backends.svn import get_updates

        try:
            commits = get_updates(self.url, self.last_rev,
                                  self.username, self.password)
        except Exception, e:
            log.exception('error during commits fetching')
            self.last_error = str(e).decode('utf-8')

            if self.last_error_date:
                interval_to_check = min(
                    max(
                        delta2secs(datetime.datetime.utcnow() - self.last_error_date) * 2,
                        CHECK_INTERVAL_MIN
                    ),
                    CHECK_INTERVAL_MAX)
            else:
                interval_to_check = CHECK_INTERVAL_MIN

            interval_to_check = datetime.timedelta(0, interval_to_check)
            log.debug('next check will be after %s' % timedelta_to_string(interval_to_check))

            self.last_error_date = datetime.datetime.utcnow()
            self.next_check_at = self.last_error_date + interval_to_check
            self.save()
            return

        for commit in commits:
            commit = Commit(**commit)
            if len(Commit.objects.find({'slug': self.slug, 'revision': commit.revision})) > 0:
                continue

            commit.slug = self.slug

            try:
                commit.save()
            except Exception:
                # just ignore this strange errors,
                # caused by wrong encoding in the comments
                # or binary files without mime type.
                log.exception('error during commit saving %s:%s' % (self.url, commit.revision))
            self.last_rev = commit.revision
            self.updated_at = commit.date


        if len(commits) > 0:
            self.last_error = None
            self.last_error_date = None

        # don't update more often than latest commits
        # TODO remove list when mongobongo will support len on cursor proxy
        latest_commits = list(Commit.objects.find({'slug': self.slug}).sort([('date', -1)])[:3])
        assert(len(latest_commits) <= 3)

        def weight(x):
            return 1.0 / (2 ** (x+1))

        if len(latest_commits) > 0:
            deltas = [
                (weight(0),
                 (datetime.datetime.utcnow() - latest_commits[0].date))
            ]

            for i in xrange(1, len(latest_commits)):
                deltas.append((weight(i), latest_commits[i-1].date - latest_commits[i].date))

            for weight, delta in deltas:
                log.debug('DELTA: %s, WEIGHT: %s' % (timedelta_to_string(delta), weight))

            interval_to_check = reduce(operator.add, (delta2secs(delta) * weight for weight, delta in deltas))

            interval_to_check = min(
                max(interval_to_check, CHECK_INTERVAL_MIN),
                CHECK_INTERVAL_MAX)
        else:
            interval_to_check = CHECK_INTERVAL_MIN

        interval_to_check = datetime.timedelta(0, interval_to_check)
        log.debug('next check will be after %s' % timedelta_to_string(interval_to_check))

        self.last_check_at = datetime.datetime.utcnow()
        self.next_check_at = self.last_check_at + interval_to_check
        self.save()

    @property
    def commits(self):
        return Commit.objects.find({'slug': self.slug})

    def update_last_access(self):
        self.last_access = datetime.datetime.utcnow()
        self.save()
        return ''



class Feed(Document):
    collection = 'feeds'



class FeedItem(Document):
    collection = 'feed_items'

    class Meta:
        ordering = [('date', DESCENDING)]



def _init_mongo_connection(sender, **kwargs):
    Repository.objects.db = mongo()

from django.db.models.signals import class_prepared
class_prepared.connect(_init_mongo_connection)


def create_feed(slug = 'test-feed'):
    feed = Feed.objects.find_one({'slug': slug})
    if feed is None:
        feed = Feed(
            slug = slug,
            ignore = [
                dict(slug = 'django', author = 'russellm'),
                dict(slug = 'stuff', author = 'depot-robot'),
                dict(slug = 'maps', author = 'aapetrov'),
            ]
        )
        feed.save()
        print 'Feed %s created' % slug

    query = ' || '.join(
        ' && '.join(
            "this.%s == '%s'" % item for item in rule.items())
            for rule in feed.ignore)

    if query:
        query = '!(%s)' % query

    FeedItem.objects.remove()
    for commit in Commit.objects.find({'$where': query}):
        FeedItem(slug = slug, date = commit.date, commit = commit).save()

