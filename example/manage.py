#!/usr/bin/env python
import sys
import os
import logging

logging.basicConfig(
    filename=os.path.join(os.path.dirname(__file__), 'example.log'),
    level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s %(pathname)s:%(lineno)d %(message)s',
    )

try:
    import settings # Assumed to be in the same directory.
except ImportError:
    import sys
    sys.stderr.write("Error: Can't find the file 'settings.py' in the directory containing %r. It appears you've customized things.\nYou'll have to run django-admin.py, passing it your settings module.\n(If the file settings.py does indeed exist, it's causing an ImportError somehow.)\n" % __file__)
    sys.exit(1)

if __name__ == "__main__":
    from django.core.management import execute_manager
    execute_manager(settings)
