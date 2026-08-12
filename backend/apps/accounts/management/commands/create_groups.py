from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        for name in ['admin', 'salesman', 'tracker', 'finance']:
            Group.objects.get_or_create(name=name)
        self.stdout.write('groups created')
