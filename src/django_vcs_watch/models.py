import os
import logging

from pdb import set_trace
from datetime import datetime

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
    strip_timezone


if 'django_globals' not in settings.INSTALLED_APPS:
    raise Exception('Please, install django_globals application.')

if 'django_globals.middleware.User' not in settings.MIDDLEWARE_CLASSES:
    raise Exception('Please, add django_globals.middleware.User to the MIDDLEWARE_CLASSES.')


class Repository(models.Model):
    user = models.ForeignKey(User, editable=False, blank=True, null=True)
    slug = models.CharField(_('Slug'), max_length=100, blank=True)
    url = models.CharField(_('URL'), max_length=255)
    last_rev = models.CharField(_('Last revision'), editable=False, max_length=32)
    last_access = models.DateTimeField(_('Last access date'), editable=False, null=True)
    created_at = models.DateTimeField(_('Created at'), editable=False)
    updated_at = models.DateTimeField(_('Updated at'), editable=False, null=True)
    public = models.BooleanField(
            _('Public'),
            default=True,
            help_text=_('Public repositories are show at the main page, when updated. Repositories which require authentication, can\'t be public.'))
    username = models.CharField(
            _('Username'), max_length=40, blank=True,
            help_text=_('Leave empty for anonymous access.'))
    password = EncryptedCharField(
            _('Password'), max_length=40, blank=True)
    last_error = models.TextField(_('Last error'), editable=False, null=True)
    last_error_date = models.DateTimeField(_('Last error\'s date'), editable=False, null=True)
    last_check_at = models.DateTimeField(_('Last check\'s date'), editable=False, null=True)
    next_check_at = models.DateTimeField(_('Next check\'s date'), editable=False, null=True)


    class Meta:
        verbose_name = _('Repository')
        verbose_name_plural = _('Repositories')
        ordering = ('-updated_at',)


    def __unicode__(self):
        return _('Repository at %s') % self.url

    def update_last_access(self):
        self.last_access = datetime.utcnow()
        self.save()
        return ''

    @models.permalink
    def get_absolute_url(self):
        return ('vcs-watch-repository', (), {'slug': self.slug})

    @models.permalink
    def get_rss_url(self):
        return ('vcs-watch-feed-commits', (), {'param': self.slug })

    def save(self):
        if not self.id:
            self.created_at = datetime.utcnow()

            from django_globals import globals
            user = getattr(globals, 'user', None)
            if isinstance(user, User):
                self.user = user
            else:
                self.public = True

        if self.username and self.password:
            self.public = False

        return super(Repository, self).save()


    def updateFeed(self):
        log = logging.getLogger('django_vcs_watch.repository.updateFeed')
        log.debug('update %s' % self.slug)

        from django_vcs_watch.backends.svn import get_updates
        try:
            commits = get_updates(self.url, self.last_rev,
                                  self.username, self.password)
        except Exception, e:
            log.exception('error during commits fetching')
            self.last_error = str(e)

            if self.last_error_date:
                interval_to_check = min(
                    max((datetime.utcnow() - self.last_error_date) * 2, CHECK_INTERVAL_MIN),
                    CHECK_INTERVAL_MAX)
            else:
                interval_to_check = CHECK_INTERVAL_MIN
            log.debug('next check will be after %s' % timedelta_to_string(interval_to_check))

            self.last_error_date = datetime.utcnow()
            self.next_check_at = self.last_error_date + interval_to_check
            self.save()
            return


        for commit in commits:
            if self.revision_set.filter(rev = commit['revision']).count() > 0:
                continue

            revision = Revision(repos   = self,
                                rev     = commit['revision'],
                                diff    = commit['diff'],
                                message = commit['message'],
                                date    = commit['date'],
                                author  = commit['author'],
                               )
            try:
                revision.save()
            except DjangoUnicodeDecodeError:
                # just ignore this strange errors,
                # caused by wrong encoding in the comments
                # or binary files without mime type.
                log.error('unicode decode exception on saving %s:%s' % (self.url, revision.rev))
            self.last_rev = revision.rev
            self.updated_at = revision.date


        if len(commits) > 0:
            self.last_error = None
            self.last_error_date = None

        # don't update more often than latest commits
        latest_revisions = self.revision_set.all()[:2]
        if len(latest_revisions) == 2:
            rev1, rev2 = latest_revisions
            interval_to_check = min(
                max(rev1.date - rev2.date, CHECK_INTERVAL_MIN),
                CHECK_INTERVAL_MAX)
        else:
            interval_to_check = CHECK_INTERVAL_MIN

        log.debug('next check will be after %s' % timedelta_to_string(interval_to_check))

        self.last_check_at = datetime.utcnow()
        self.next_check_at = self.last_check_at + interval_to_check
        self.save()



class Revision(models.Model):
    repos = models.ForeignKey(Repository)
    rev = models.CharField(name=_('Revision'), max_length=36)
    author = models.CharField(name=_('Author'), max_length=40)
    date = models.DateTimeField(name=_('Date'))
    message = models.TextField(name=_('Message'))
    diff = models.TextField(name=_('Diff'))

    def __unicode__(self):
        return _('Revision %(rev)s by %(author)s') % self.__dict__

    @models.permalink
    def get_absolute_url(self):
        return ('vcs-watch-revision', (), {'repository_slug': self.repos.slug, 'revision': self.rev})

    class Meta:
        ordering = ('-date',)

