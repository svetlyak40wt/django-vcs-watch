import re

# URL rewriters
_http_re = re.compile(r'^(https|http)')

def to_svn_ssh(url):
    return _http_re.sub('svn+ssh', url)

def remove_wsvn(url):
    return url.replace('/websvn/wsvn', '')

def strip_get(url):
    return url.split('?', 1)[0]
