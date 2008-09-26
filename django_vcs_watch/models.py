import os
import uuid

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
    hash = models.CharField(name='Hash', editable=False, max_length=36)
    url = models.URLField(name='URL', verify_exists=False)
    last_rev = models.CharField(name='Last revision', editable=False, max_length=32)
    last_access = models.DateTimeField(name='Date', editable=False, null=True)
    public = models.BooleanField(name='Public', default=True)

    class Meta:
        verbose_name = 'Repository'
        verbose_name_plural = 'Repositories'

    def save(self):
        if self.id is None:
            self.hash = unicode(uuid.uuid4())
        return super(Repository, self).save()

    def updateFeed(self):
        log = open('/tmp/log.txt', 'a')
        log.write('update %s\n' % self.hash)

        limit = rev = ''

        if self.last_rev:
            rev = ' -r HEAD:%s ' % self.last_rev

        if _REVISION_LIMIT:
            limit = ' --limit %s ' % _REVISION_LIMIT

        command = 'svn log %(limit)s %(rev)s --xml %(url)s' % {
                'rev': rev,
                'limit': limit,
                'url': self.url
                }
        print command
        in_, out_ = os.popen2(command)

        xml = out_.read()
        #print xml
        if not xml:
            return

        try:
            xml_e = ET.fromstring(xml)
        except Exception, e:
            print e
            return

        diffs = []
        for entry_e in xml_e.findall('logentry'):
            revision = entry_e.attrib['revision']
            if self.revision_set.filter(rev=revision).count() > 0:
                continue

            author = entry_e.find('author').text
            msg = entry_e.find('msg').text
            date = parse_date(entry_e.find('date').text).astimezone(tzutc())

            print revision, author
            print msg
            in_, out_ = os.popen2('svn diff -c %s %s' % (revision, self.url))
            diff = out_.read()
            #print diff

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

        self.save()


class Revision(models.Model):
    repos = models.ForeignKey(Repository)
    rev = models.CharField(name='Revision', max_length=36)
    author = models.CharField(name='Author', max_length=40)
    date = models.DateTimeField(name='Date')
    message = models.TextField(name='Message')
    diff = models.TextField(name='Diff')

    class Meta:
        ordering = ('-date',)

