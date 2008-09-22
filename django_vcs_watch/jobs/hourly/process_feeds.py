from django_extensions.management.jobs import BaseJob

class Job(BaseJob):
    help = "My sample job."

    def execute(self):
        open('/tmp/job.txt', 'w').write('blah')
