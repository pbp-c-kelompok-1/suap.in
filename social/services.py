from datetime import timedelta

from django.contrib.auth.models import User
from django.db.models import Count, F, Q
from django.utils import timezone

from .models import University

XP_PER_SCAN = 10  # sementara (PRD: +10 XP per scan). Ganti ke data XP modul gamifikasi kalau sudah ada.


def week_start():
    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


def month_start():
    return timezone.localdate().replace(day=1)


def ranked_users(since):
    scans = Count('food_logs', filter=Q(food_logs__scanned_at__date__gte=since))
    return (
        User.objects.annotate(scans=scans)
        .annotate(xp=F('scans') * XP_PER_SCAN)
        .filter(xp__gt=0)
        .select_related('campus__university')
        .order_by('-xp', 'username')
    )


def ranked_campuses(since):
    scans = Count(
        'members__user__food_logs',
        filter=Q(members__user__food_logs__scanned_at__date__gte=since),
    )
    campuses = list(
        University.objects.annotate(
            member_count=Count('members', distinct=True),
            scans=scans,
        ).annotate(total_xp=F('scans') * XP_PER_SCAN)
    )
    for c in campuses:
        c.avg_xp = round(c.total_xp / c.member_count, 1) if c.member_count else 0
    campuses.sort(key=lambda c: (-c.avg_xp, c.short_name))
    return campuses
