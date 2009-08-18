import re

# URL rewriters
_http_re = re.compile(r'^(https|http)')

def to_svn_ssh(url):
    return _http_re.sub('svn+ssh', url)

def remove_wsvn(url):
    return url.replace('/websvn/wsvn', '')

def strip_get(url):
    return url.split('?', 1)[0]

# slugificator

def make_slugs(url):
    "Returns list of available slugs for given URL."
    from urlparse import urlparse
    host, path = urlparse(url)[1:3]
    host = [host.split('.')[-2]]
    path = filter(lambda x:x, path.replace('.', '-').split('/'))

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
    base = path

    result = [
        path,
        host + path
    ]

    return ['-'.join(slug) for slug in result if slug]

def strip_timezone(t):
    return datetime(t.year, t.month, t.day, t.hour, t.minute, t.second, t.microsecond)

def timedelta_to_string(td):
    return '%d days, %d hours, %d minutes, %d seconds' % (
        td.days,
        td.seconds / 3600,
        td.seconds % 3600 / 60,
        td.seconds % 60
    )

