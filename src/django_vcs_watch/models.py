import os
import uuid
import logging
import re
import subprocess

from pdb import set_trace
from datetime import datetime, timedelta
from dateutil.parser import parse as parse_date
from dateutil.tz import tzutc

from xml.etree import ElementTree as ET

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import DjangoUnicodeDecodeError, force_unicode

from django_fields.fields import EncryptedCharField

_REVISION_LIMIT = getattr(settings, 'VCS_REVISION_LIMIT', 20)


if 'django_globals' not in settings.INSTALLED_APPS:
    raise Exception('Please, install django_globals application.')

if 'django_globals.middleware.User' not in settings.MIDDLEWARE_CLASSES:
    raise Exception('Please, add django_globals.middleware.User to the MIDDLEWARE_CLASSES.')

def guess_encoding(s):
    options = [
        {}, {'encoding': 'cp1251'}, {'encoding': 'koi8-r'},
        {'encoding': 'utf-8', 'errors': 'ignore'}
    ]
    for o in options:
        try:
            return force_unicode(s, **o)
        except DjangoUnicodeDecodeError:
            pass
    raise Exception('Can\'t decode string: %r' % s)

def strip_timezone(t):
    return datetime(t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond)

class Repository(models.Model):
    user = models.ForeignKey(User, editable=False, blank=True, null=True)
    hash = models.CharField(_('Hash'), editable=False, max_length=36)
    url = models.URLField(_('URL'), verify_exists=False)
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


    class Meta:
        verbose_name = _('Repository')
        verbose_name_plural = _('Repositories')
        ordering = ('-updated_at',)


    def __unicode__(self):
        return _('Repository at %s') % self.url

    def update_last_access(self):
        self.last_access = datetime.today()
        self.save()
        return ''

    @models.permalink
    def get_absolute_url(self):
        return ('vcs-watch-repository', (), {'slug': self.hash})

    @models.permalink
    def get_rss_url(self):
        return ('vcs-watch-feeds', (), {'url': 'diffs/%s' % self.hash })

    def save(self):
        if not self.id:
            self.hash = unicode(uuid.uuid4())
            self.created_at = datetime.today()

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
        logger = logging.getLogger('django_vcs_watch.repository.updateFeed')

        need_to_update = True
        interval_to_check = timedelta(0, getattr(settings, 'VCS_WATCH_CHECK_INTERVAL', 60)*60)

        # don't update more often than latest commits
        if self.last_check_at is not None:
            latest_revisions = self.revision_set.all()[:2]
            if len(latest_revisions) == 2:
                rev1, rev2 = latest_revisions
                interval_to_check = rev1.date - rev2.date

            logger.debug('interval to check %r, last_check %r' % (interval_to_check, self.last_check_at))
            if (datetime.today() - self.last_check_at) < interval_to_check:
                need_to_update = False

        # wait for hour after error
        elif self.last_error_date is not None and \
             ((datetime.today() - self.last_error_date) < interval_to_check):
             need_to_update = False

        if not need_to_update:
            logger.debug('no need to update %s' % self.hash)
            return


        logger.debug('update %s' % self.hash)

        command = ['svn', 'log', '--non-interactive']

        if self.last_rev:
            command += ['-r', 'HEAD:%s' % self.last_rev]

        if _REVISION_LIMIT:
            command += ['--limit', '%s' % _REVISION_LIMIT]

        if self.username:
            command += ['--username', self.username]

        if self.password:
            command += ['--password', self.password]

        command += ['--xml', self.url]

        logger.debug(re.sub(r"--password '.*'", "--password 'xxxxx'", ' '.join(command)))

        svn = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        xml, stderr = svn.communicate()

        if svn.returncode != 0 or stderr or not xml:
            logger.error('svn command failed with code %d and message %r' % (svn.returncode, stderr))
            self.last_error = '<br />'.join(stderr.splitlines())
            self.last_error_date = datetime.today()
            self.save()
            return

        try:
            xml_e = ET.fromstring(xml)
        except Exception, e:
            logger.error(e)
            logger.error(xml)
            return

        diffs = []
        for entry_e in xml_e.findall('logentry'):
            revision = entry_e.attrib['revision']
            if self.revision_set.filter(rev=revision).count() > 0:
                continue

            author = entry_e.find('author').text
            msg = entry_e.find('msg').text
            date = parse_date(entry_e.find('date').text).astimezone(tzutc())

            command = ['svn', 'diff', '-c', str(revision), self.url]
            logger.debug('fetching diff: %r' % ' '.join(command))

            svn = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            diff, stderr = svn.communicate()

            diffs.append( Revision(repos = self,
                               rev = revision,
                               diff=guess_encoding(diff),
                               message=msg or u'',
                               date=strip_timezone(date),
                               author=author
                               )
                        )

        for diff in reversed(diffs):
            logger.debug('saving %s r%s' % (self.url, diff.rev))
            try:
                diff.save()
            except DjangoUnicodeDecodeError:
                # just ignore this strange errors,
                # caused by wrong encoding in the comments
                # or binary files without mime type.
                logger.error('unicode decode exception on saving %s:%s' % (self.url, diff.rev))
            self.last_rev = diff.rev
            self.updated_at = diff.date


        if len(diffs) > 0:
            self.last_error = None
            self.last_error_date = None

        for old_revision in self.revision_set.all()[_REVISION_LIMIT:]:
            old_revision.delete()

        self.last_check_at = datetime.today()
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
        return ('vcs-watch-revision', (), {'repository_hash': self.repos.hash, 'revision': self.rev})

    class Meta:
        ordering = ('-date',)

