import os
import uuid
import logging
import re

from pdb import set_trace
from datetime import datetime
from dateutil.parser import parse as parse_date
from dateutil.tz import tzutc

from xml.etree import ElementTree as ET

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.utils.encoding import DjangoUnicodeDecodeError

from django_fields.fields import EncryptedCharField

_REVISION_LIMIT = getattr(settings, 'VCS_REVISION_LIMIT', 20)


if 'django_globals' not in settings.INSTALLED_APPS:
    raise Exception('Please, install django_globals application.')

if 'django_globals.middleware.User' not in settings.MIDDLEWARE_CLASSES:
    raise Exception('Please, add django_globals.middleware.User to the MIDDLEWARE_CLASSES.')

def strip_timezone(t):
    return datetime(t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond)

class Repository(models.Model):
    user = models.ForeignKey(User, editable=False, blank=True, null=True)
    hash = models.CharField(_('Hash'), editable=False, max_length=36)
    url = models.URLField(_('URL'), verify_exists=False)
    last_rev = models.CharField(_('Last revision'), editable=False, max_length=32)
    last_access = models.DateTimeField(_('Last access date'), editable=False, null=True)
    created_at = models.DateTimeField(_('Created at'), editable=False)
    updated_at = models.DateTimeField(_('Updated at'), editable=False)
    public = models.BooleanField(
            _('Public'),
            default=True,
            help_text=_('Public repositories are show at the main page, when updated. Repositories which require authentication, can\'t be public.'))
    username = models.CharField(
            _('Username'), max_length=40, blank=True,
            help_text=_('Leave empty for anonymous access.'))
    password = EncryptedCharField(
            _('Password'), max_length=40, blank=True)


    class Meta:
        verbose_name = _('Repository')
        verbose_name_plural = _('Repositories')
        ordering = ('-updated_at',)


    def __unicode__(self):
        return _('Repository at %s') % self.url

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
        logger = logging.getLogger('django_vcs_view.repository.updateFeed')

        logger.debug('update %s' % self.hash)

        options = {
            'url': self.url,
            'rev':'', 'limit':'', 'username':'', 'password':''
        }

        if self.last_rev:
            options['rev'] = ' -r HEAD:%s ' % self.last_rev

        if _REVISION_LIMIT:
            options['limit'] = ' --limit %s ' % _REVISION_LIMIT

        if self.username:
            options['username'] = ' --username \'%s\' ' % self.username

        if self.password:
            options['password'] = ' --password \'%s\' ' % self.password

        command = 'svn log --non-interactive %(limit)s%(rev)s%(username)s%(password)s --xml %(url)s' % options

        logger.debug(re.sub(r"--password '.*'", "--password 'xxxxx'", command))

        in_, out_ = os.popen2(command)

        xml = out_.read()
        if not xml:
            return

        try:
            xml_e = ET.fromstring(xml)
        except Exception, e:
            logger.error(e)
            return

        diffs = []
        for entry_e in xml_e.findall('logentry'):
            revision = entry_e.attrib['revision']
            if self.revision_set.filter(rev=revision).count() > 0:
                continue

            author = entry_e.find('author').text
            msg = entry_e.find('msg').text
            date = parse_date(entry_e.find('date').text).astimezone(tzutc())

            logger.debug('fetching revision %s by %s' % (revision, author))

            in_, out_ = os.popen2('svn diff -c %s %s' % (revision, self.url))
            diff = out_.read()

            diffs.append( Revision(repos = self,
                               rev = revision,
                               diff=diff,
                               message=msg or '',
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
            self.save()

        for old_revision in self.revision_set.all()[_REVISION_LIMIT:]:
            old_revision.delete()


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

