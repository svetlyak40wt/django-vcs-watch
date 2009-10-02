import re
import md5
from datetime import datetime

from django.conf import settings
from django.utils.encoding import DjangoUnicodeDecodeError, force_unicode

# URL rewriters
_http_re = re.compile(r'^(https|http)')

def to_svn_ssh(url):
    return _http_re.sub('svn+ssh', url)

def remove_wsvn(url):
    return url.replace('/websvn/wsvn', '')

def strip_get(url):
    return url.split('?', 1)[0]

# slugificator

def make_slug(url, path_filter = lambda x: x not in ['', 'svn']):
    "Returns a slug for given URL."
    from urlparse import urlparse
    host, path = urlparse(url)[1:3]
    host = host.split('.')

    result = []

    if host[-2] == 'googlecode':
        result.append(host[-3])

    path = filter(path_filter, path.replace('.', '-').split('/'))

    def index(l, value):
        try: return l.index(value)
        except ValueError: return None

    ttb_index = filter(lambda x: x is not None, [
        index(path, 'trunk'),
        index(path, 'tags'),
        index(path, 'branches'),
    ])

    if ttb_index:
        path.pop(ttb_index[0])
    result += path

    if len(result) == 0:
        result.append(host[-2])

    return '-'.join(result)


def strip_timezone(t):
    return datetime(t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond)


def timedelta_to_string(td):
    return '%d days, %d hours, %d minutes, %d seconds' % (
        td.days,
        td.seconds / 3600,
        td.seconds % 3600 / 60,
        td.seconds % 60
    )


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

def mongo():
    from pymongo.connection import Connection
    from django_vcs_watch.settings import \
        MONGO_URL, \
        MONGO_DB

    conn = Connection(MONGO_URL)
    return conn[MONGO_DB]


def get_user_feed_slug(user):
    if user.is_anonymous():
        raise Exception("Anonymous user can't have a feed.")
    return md5.md5(user.username + settings.SECRET_KEY).hexdigest()


class DiffProcessor(object):
    """Helper to parse diffs, separate by file and collect some information."""

    def _start_new_file(self, filename):
        if self.current is not None:
            self.current['diff'] = '\n'.join(self.current['diff'])
            self.changed.append(self.current)

        self.current = dict(
            filename = filename,
            diff = [],
            stats = dict(added = 0, removed = 0)
        )


    def process(self, diff):
        """Parses diff and returns dict with statistics and separate diffs for each changed file."""
        self.changed = []
        self.current = None
        self.added = 0
        self.removed = 0

        for line in diff.split('\n'):
            if line.startswith('Index: '):
                self._start_new_file(line.split(' ', 1)[1])
                continue
            elif line[:3] in ('===', '---', '+++'):
                continue
            elif line.startswith('+'):
                self.added += 1
                self.current['stats']['added'] += 1
            elif line.startswith('-'):
                self.removed -= 1
                self.current['stats']['removed'] -= 1

            if self.current is not None:
                self.current['diff'].append(line)

        self._start_new_file(None)

        return dict(
                changed = self.changed,
                stats = dict(
                        added = self.added,
                        removed = self.removed
                    )
            )

