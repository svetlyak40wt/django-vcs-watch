Django VCS Watch
================

This is a django application which serve as RSS proxy for different VCSs.

Dependencies
============

Required
--------

django_globals is required to automatic update of the 'user' field.

To install django_global, download it's sources and install this
package somewhere in your python path.

Then, add 'django_global' in to the INSTALLED_APPS, and add
'django_globals.middleware.User' into the MIDDLEWARE_CLASSES.

Optional
--------

There are some test templates in the templates/django_vcs_watch.
They use modified 'Colorize' filter by [Will Larson](http://lethain.com/author/will-larson/),
but you can use another colorizer in your own templates.

