from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from challenge.reports import build_report_history


class Command(BaseCommand):
    help = 'Generate missing persisted WeeklyReport snapshots for all users.'

    def handle(self, *args, **options):
        today = timezone.localdate()
        User = get_user_model()
        count = 0
        for user in User.objects.iterator():
            build_report_history(user, today=today)
            count += 1
        self.stdout.write(self.style.SUCCESS(
            f'Weekly reports generated/updated for {count} users.'
        ))
