#!/usr/bin/env python
import sys
import logging

logging.basicConfig(filename='/tmp/vcs_watch.log', level=logging.DEBUG)

sys.path.append('/home/art/my-apps')
sys.path.append('/home/art/contrib-apps')
sys.path.append('/home/art/django-unicode')

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    from django.core.management import execute_manager
    execute_manager(settings)
