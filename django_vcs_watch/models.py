import os
import uuid
import logging
import re

from datetime import datetime
from dateutil.parser import parse as parse_date
from dateutil.tz import tzutc

from xml.etree import ElementTree as ET

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User

_REVISION_LIMIT = getattr(settings, 'VCS_REVISION_LIMIT', 20)


def strip_timezone(t):
    return datetime(t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond)

class Repository(models.Model):
    user = models.ForeignKey(User, editable=False, null=True)
    hash = models.CharField('Hash', editable=False, max_length=36)
    url = models.URLField('URL', verify_exists=False)
    last_rev = models.CharField('Last revision', editable=False, max_length=32)
    last_access = models.DateTimeField('Last access date', editable=False, null=True)
    created_at = models.DateTimeField('Created at', editable=False)
    updated_at = models.DateTimeField('Updated at', editable=False)
    public = models.BooleanField(
            'Public',
            default=True,
            help_text='Repositories which require authentication, can\'t be public.')
    username = models.CharField(
            'Username', max_length=40, blank=True,
            help_text='Leave empty for anonymous access.')
    password = models.CharField(
            'Password', max_length=40, blank=True)

    class Meta:
        verbose_name = 'Repository'
        verbose_name_plural = 'Repositories'
        ordering = ('-updated_at',)


    def __unicode__(self):
        return 'Repository at %s' % self.url

    def get_absolute_url(self):
        return '/vcs/%s/' % self.hash

    @models.permalink
    def get_rss_url(self):
        return ('vcs-watch-feeds', (), {'url': 'diffs/%s' % self.hash })

    def save(self):
        seld.updated_at = datetime.today()

        if not self.id:
            self.hash = unicode(uuid.uuid4())
            self.created_at = self.updated_at

        if self.username and self.password:
            self.public = False

        return super(Repository, self).save()

    def updateFeed(self):
        logger = logging.getLogger('django_vcs_view.repository.updateFeed')

        logger.debug('update %s\n' % self.hash)

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

        command = 'svn log %(limit)s%(rev)s%(username)s%(password)s --xml %(url)s' % options

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
                               message=msg,
                               date=strip_timezone(date),
                               author=author
                               )
                        )

        for diff in reversed(diffs):
            diff.save()
            self.last_rev = diff.rev

        for old_revision in self.revision_set.all()[_REVISION_LIMIT:]:
            old_revision.delete()

        self.save()


class Revision(models.Model):
    repos = models.ForeignKey(Repository)
    rev = models.CharField(name='Revision', max_length=36)
    author = models.CharField(name='Author', max_length=40)
    date = models.DateTimeField(name='Date')
    message = models.TextField(name='Message')
    diff = models.TextField(name='Diff')

    def __unicode__(self):
        return 'Revision %s' % self.rev

    def get_absolute_url(self):
        return '/vcs/%s/%s/' % (self.repos.hash, self.rev)

    class Meta:
        ordering = ('-date',)

