Django VCS Watch
----------------

This is a django application which serve as RSS proxy for different VCSs.

Dependencies
============

### Required ###

**django_globals** is required to automatic update of the 'user' field.

To install `django_globals`, download sources from a repository
<http://github.com/svetlyak40wt/django-globals/> and install
package `django_globals` somewhere in your python path.

Then, add `django_globals` in to the `INSTALLED_APPS`, and add
`django_globals.middleware.User` into the `MIDDLEWARE_CLASSES`.

**django_fields** required for encrypted passwords and authentication.
You can find it at <http://github.com/svetlyak40wt/django-fields>, also,
it have it's own dependencies, for example, from django-pycrypto.

**python-dateutil** this package used to parse ISO dates.
Under *debian* like systems, just do `sudo apt-get install python-dateutil`


### Optional ###

There are some test templates in the `templates/django_vcs_watch`.
They use modified 'Colorize' filter by [Will Larson](http://lethain.com/author/will-larson/),
but you can use another colorizer in your own templates.

Example
=======

Example project is in the `example` directory.

Options
=======

These options can be added to your settings.py:

* `VCS_WATCH_CHECK_INTERVAL` -- Interval in minutes, to check feeds for updated.
  In case if there is no any information about feed, it will be polled for updates
  with this frequency. If there are two or more commits already fetched, then,
  check interval will be interval between two latest commits, so that more actively
  developed projects will be polled more oftenly. **Default value is 60 minutes.**

* `VCS_WATCH_PID_DIR` -- Directory, where to story pid file for jobs.
  **Default value is '/tmp'.**

* `VCS_ONLY_PUBLIC_REPS` -- Set to True if you want only public repositories online.

TODO
====

* Write a short *Installation* instruction.
* Add check for valid and accessible URL before add it to database.
* Add ability to edit or remove Repository.

