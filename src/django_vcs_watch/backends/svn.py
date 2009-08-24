import re
import logging
import subprocess
from dateutil.parser import parse as parse_date
from dateutil.tz import tzutc
from xml.etree import ElementTree as ET

from django_vcs_watch.utils import \
    strip_timezone, \
    guess_encoding, \
    DiffProcessor

from django_vcs_watch.settings import \
    REVISION_LIMIT

def get_updates(url, last_rev, username = None, password = None):
    log = logging.getLogger('django_vcs_watch.backend.svn')

    command = ['svn', 'log', '--non-interactive']

    if last_rev:
        command += ['-r', 'HEAD:%s' % last_rev]

    command += ['--limit', '%s' % REVISION_LIMIT]

    if username:
        command += ['--username', username]

    if password:
        command += ['--password', password]

    command += ['--xml', url]

    log.debug(re.sub(r"--password '.*'", "--password 'xxxxx'", ' '.join(command)))

    svn = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    xml, stderr = svn.communicate()

    if svn.returncode != 0 or stderr or not xml:
        log.error('svn command failed with code %d and message %r' % (svn.returncode, stderr))
        raise Exception(' '.join(stderr.splitlines()))

    xml_e = ET.fromstring(xml)

    commits = []
    diff_processor = DiffProcessor()

    for entry_e in xml_e.findall('logentry'):
        revision = entry_e.attrib['revision']
        if revision == last_rev:
            continue

        author = entry_e.find('author').text
        msg = entry_e.find('msg').text
        date = parse_date(entry_e.find('date').text).astimezone(tzutc())

        command = ['svn', 'diff', '-c', str(revision), url]
        log.debug('fetching diff: %r' % ' '.join(command))

        svn = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        diff, stderr = svn.communicate()

        commits.insert(0, dict(
                           revision = revision,
                           changes = diff_processor.process(guess_encoding(diff)),
                           message = msg or u'',
                           date = strip_timezone(date),
                           author = author
                           )
                    )
    return commits

