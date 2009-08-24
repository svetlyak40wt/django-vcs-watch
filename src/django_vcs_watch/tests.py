from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from django_vcs_watch.models import Repository
from django_vcs_watch.utils import make_slug, DiffProcessor, mongo
from django_vcs_watch.settings import VCS_ONLY_PUBLIC_REPS

from pdb import set_trace

class _RepsTestCase(TestCase):
    def setUp(self):
        try:
            self.tester = User.objects.get(username='tester')
        except User.DoesNotExist:
            self.tester = User.objects.create_user(username='tester', email='tester@example.com', password='test')

        self.add_url = reverse('vcs-watch-add')
        self.login_url = reverse('vcs-watch-add')

        Repository.objects.db = mongo()
        Repository.objects.remove({})
        super(_RepsTestCase, self).setUp()

class Repositories(_RepsTestCase):
    def testGetAnonymousForm(self):
        response = self.client.get(self.add_url)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'id_url')
        self.assertContains(response, 'id_slug')

    def testAddRepByAnonymous(self):
        url = 'http://svn.example.com/trunk/'
        response = self.client.post(self.add_url, dict(url=url))

        reps = list(Repository.objects.find())
        self.assertEqual(1, len(reps))
        self.assertEqual(url, reps[0]['url'])
        self.assertEqual(True, reps[0]['public'])

        url = reverse('vcs-watch-repository', kwargs = dict(slug=reps[0]['slug']))
        self.assertRedirects(response, url)

    def testAddRepTwice(self):
        url = 'http://svn.example.com/trunk/'
        response = self.client.post(self.add_url, dict(url=url))
        response = self.client.post(self.add_url, dict(url=url))

        reps = list(Repository.objects.all())
        self.assertEqual(1, len(reps))
        self.assertEqual(url, reps[0]['url'])
        self.assertEqual(True, reps[0]['public'])
        self.assertEqual(u'example', reps[0]['slug'])

        url = reverse('vcs-watch-repository', kwargs = dict(slug=reps[0]['slug']))
        self.assertRedirects(response, url)

if not VCS_ONLY_PUBLIC_REPS:
    class PrivateRepositories(_RepsTestCase):
        def testGetNonAnonymousForm(self):
            self.assert_(self.client.login(username='tester', password='test'))

            response = self.client.get(self.add_url)
            self.assertEqual(200, response.status_code)
            self.assertContains(response, 'id_url')
            self.assertContains(response, 'id_public')
            self.assertContains(response, 'id_username')
            self.assertContains(response, 'id_password')

        def testAddByAuthorized(self):
            self.assert_(self.client.login(username='tester', password='test'))
            url = 'http://svn.example.com/trunk/'
            response = self.client.post(self.add_url, dict(
                                            url=url,
                                            username='svnuser',
                                            password='svnpass',
                                            ))

            reps = list(Repository.objects.all())
            self.assertEqual(1, len(reps))
            self.assertEqual(url, reps[0]['url'])
            self.assertEqual(False, reps[0]['public'])
            self.assertEqual('svnuser', reps[0]['username'])
            self.assertEqual('svnpass', reps[0]['password'])

            url = reverse('vcs-watch-repository', kwargs = dict(slug=reps[0]['slug']))
            self.assertRedirects(response, url)

        def testPrivateReposList(self):
            self.assert_(self.client.login(username='tester', password='test'))

            url = 'http://svn.example.com/trunk/'
            slugs = []
            for i in xrange(10):
                response = self.client.post(self.add_url, dict(
                                                url=url,
                                                username='svnuser',
                                                password='svnpass',
                                                ))
                slugs.append(response.get('Location', None).split('/')[-2])

            user_url = reverse('vcs-watch-profile')
            response = self.client.get(user_url)
            self.assertEqual(200, response.status_code)

            for slug in slugs:
                self.assertContains(response, slug)


class Rewrites(TestCase):
    def testSSH(self):
        from django_vcs_watch.utils import to_svn_ssh

        self.assertEqual('svn+ssh://svn.example.com/test',
              to_svn_ssh('http://svn.example.com/test'))

        self.assertEqual('svn+ssh://svn.example.com/test',
              to_svn_ssh('https://svn.example.com/test'))


    def testWSVN(self):
        from django_vcs_watch.utils import remove_wsvn

        self.assertEqual('https://svn.example.org/auto',
             remove_wsvn('https://svn.example.org/websvn/wsvn/auto'))

    def testStripGET(self):
        from django_vcs_watch.utils import strip_get

        self.assertEqual('https://svn.example.org/auto',
               strip_get('https://svn.example.org/auto?'))

class Slugs(TestCase):
    def testMakeSlugs(self):
        self.assertEqual(
            'django',
            make_slug('http://svn.example.com/django/trunk/'))

        self.assertEqual(
            'example',
            make_slug('http://svn.example.com'))
        self.assertEqual(
            'example',
            make_slug('http://svn.example.com/trunk/'))
        self.assertEqual(
            'django-django-contrib',
            make_slug('http://svn.example.com/django/trunk/django/contrib/'))
        self.assertEqual(
            'django-new-admin',
            make_slug('http://svn.example.com/django/branches/new-admin/'))
        self.assertEqual(
            'django-1-1',
            make_slug('http://svn.example.com/django/tags/1.1/'))
        self.assertEqual(
            'mock',
            make_slug('http://mock.googlecode.com/svn/'))
        self.assertEqual(
            'django-grappelli-2-5',
            make_slug('http://django-grappelli.googlecode.com/svn/branches/2.5'))


class DiffProcessing(TestCase):
    def testSeparate(self):
        diff = """
Index: django/db/backends/oracle/introspection.py
===================================================================
--- django/db/backends/oracle/introspection.py  (revision 11474)
+++ django/db/backends/oracle/introspection.py  (revision 11475)
@@ -26,6 +26,14 @@
     except AttributeError:
         pass
  
+    def get_field_type(self, data_type, description):
+        # If it's a NUMBER with scale == 0, consider it an IntegerField
+        if data_type == cx_Oracle.NUMBER and description[5] == 0:
+            return 'IntegerField'
+        else:
+            return super(DatabaseIntrospection, self).get_field_type(
+                data_type, description)
+ 
     def get_table_list(self, cursor):
         \"Returns a list of table names in the current database.\"
         cursor.execute(\"SELECT TABLE_NAME FROM USER_TABLES\")
Index: django/db/backends/__init__.py
===================================================================
--- django/db/backends/__init__.py      (revision 11474)
+++ django/db/backends/__init__.py      (revision 11475)
@@ -470,6 +470,14 @@
     def __init__(self, connection):
         self.connection = connection

+    def get_field_type(self, data_type, description):
+        \"\"\"Hook for a database backend to use the cursor description to
+        match a Django field type to a database column.
+
+        For Oracle, the column data_type on its own is insufficient to
+        distinguish between a FloatField and IntegerField, for example.\"\"\"
+        return self.data_types_reverse[data_type]
+
     def table_name_converter(self, name):
         \"\"\"Apply a conversion to the name for the purposes of comparison.

@@ -560,4 +568,3 @@
     def validate_field(self, errors, opts, f):
         \"By default, there is no backend-specific validation\"
         pass
-
Index: django/core/management/commands/inspectdb.py
===================================================================
--- django/core/management/commands/inspectdb.py        (revision 11474)
+++ django/core/management/commands/inspectdb.py        (revision 11475)
@@ -73,7 +73,7 @@
                         extra_params['db_column'] = column_name
                 else:
                     try:
-                        field_type = connection.introspection.data_types_reverse[row[1]]
+                        field_type = connection.introspection.get_field_type(row[1], row)
                     except KeyError:
                         field_type = 'TextField'
                         comment_notes.append('This field type is a guess.')
"""



        processor = DiffProcessor()
        result = processor.process(diff)
        self.assertEqual(3, len(result['changed']))
        self.assertEqual([
                'django/db/backends/oracle/introspection.py',
                'django/db/backends/__init__.py',
                'django/core/management/commands/inspectdb.py',
            ], [file['filename'] for file in result['changed']])
        self.assertEqual(17, result['stats']['added'])
        self.assertEqual(-2, result['stats']['removed'])
        self.assert_(unicode, type(result['changed'][0]['diff']))

        self.assertEqual(8, result['changed'][0]['stats']['added'])
        self.assertEqual(0, result['changed'][0]['stats']['removed'])
        self.assertEqual(8, result['changed'][1]['stats']['added'])
        self.assertEqual(-1, result['changed'][1]['stats']['removed'])
        self.assertEqual(1, result['changed'][2]['stats']['added'])
        self.assertEqual(-1, result['changed'][2]['stats']['removed'])

