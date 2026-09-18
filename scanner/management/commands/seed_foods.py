from django.core.management.base import BaseCommand
from django.core.management import call_command


class Command(BaseCommand):
    help = 'Load 55 initial food items into database'

    def handle(self, *args, **options):
        self.stdout.write('Loading food fixtures...')
        call_command('loaddata', 'scanner/fixtures/foods.json')
        self.stdout.write(self.style.SUCCESS('Done. 55 food items loaded.'))
