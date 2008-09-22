import uuid

from django.db import models

class Repository(models.Model):
    hash = models.CharField(name='Hash', editable=False, max_length=36)
    url = models.URLField(name='URL', verify_exists=False)
    last_rev = models.CharField(name='Last revision', editable=False, max_length=32)

    class Meta:
        verbose_name = 'Repository'
        verbose_name_plural = 'Repositories'

    def save(self):
        if self.id is None:
            self.hash = unicode(uuid.uuid1())
        return super(Repository, self).save()

class Diff(models.Model):
    repos = models.ForeignKey(Repository)
    rev = models.CharField(name='Revision', max_length=32)
    diff = models.TextField(name='Diff')

