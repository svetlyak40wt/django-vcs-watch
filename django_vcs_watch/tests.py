from django.test import TestCase
from django.test.client import Client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from models import Repository

from pdb import set_trace

class Repositories(TestCase):
    def setUp(self):
        try:
            self.tester = User.objects.get(username='tester')
        except User.DoesNotExist:
            self.tester = User.objects.create_user(username='tester', email='tester@example.com', password='test')

        self.add_url = reverse('vcs-watch-add')

        Repository.objects.all().delete()
        super(Repositories, self).setUp()

    def testGetAnonymousForm(self):
        response = self.client.get(self.add_url)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'id_url')
        self.assertNotContains(response, 'id_public')
        self.assertNotContains(response, 'id_username')

    def testGetNonAnonymousForm(self):
        self.assert_(self.client.login(username='tester', password='test'))

        response = self.client.get(self.add_url)
        self.assertEqual(200, response.status_code)
        self.assertContains(response, 'id_url')
        self.assertContains(response, 'id_public')
        self.assertContains(response, 'id_username')
        self.assertContains(response, 'id_password')

    def testAddRepByAnonymous(self):
        url = 'http://svn.example.com/trunk/'
        response = self.client.post(self.add_url, dict(url=url))

        reps = Repository.objects.all()
        self.assertEqual(1, len(reps))
        self.assertEqual(url, reps[0].url)
        self.assertEqual(True, reps[0].public)

        url = reverse('vcs-watch-repository', kwargs = dict(slug=reps[0].hash))
        self.assertRedirects(response, url)

