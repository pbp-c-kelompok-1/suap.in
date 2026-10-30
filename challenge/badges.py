"""Lencana untuk Statistik & Lencana di Challenge.

Semuanya hidup di app challenge: model Badge dan UserBadge milik gamification
hanya dibaca/ditulis barisnya, kode gamification tidak diubah.

- ensure_badges(): membuat lencana dari daftar milestone bila belum ada, dan
  mencatat tanggal rilisnya (BadgeRelease) untuk notifikasi "lencana baru".
- award_badges(): memberi lencana yang syaratnya sudah terpenuhi. Scan dihitung
  per FOTO (sama dengan angka "Total scan"), bukan per item makanan.
"""
from datetime import datetime, timezone as dt_timezone

from django.utils import timezone

from gamification import services as game
from gamification.models import Badge, UserBadge
from scanner.models import FoodLog

from .models import BadgeRelease

LONG_AGO = datetime(2020, 1, 1, tzinfo=dt_timezone.utc)


def ensure_badges():
    """Aman dipanggil berulang. Mengembalikan jumlah lencana yang baru dibuat/dicatat."""
    wanted = []
    for m in game.STREAK_MILESTONES:
        wanted.append(dict(code=f"{m}-streak", name=f"{m} Day Streak",
                           description=f"Mempertahankan streak selama {m} hari",
                           icon='flame', criteria_type='streak_duration', threshold=m))
    for m in game.SCAN_MILESTONES:
        wanted.append(dict(code=f"{m}-scans", name=f"{m} Scans",
                           description=f"Melakukan scan sebanyak {m}x",
                           icon='camera', criteria_type='scan_amount', threshold=m))

    existing = set(Badge.objects.values_list('code', flat=True))
    new = [Badge(**w) for w in wanted if w['code'] not in existing]
    if new:
        Badge.objects.bulk_create(new, ignore_conflicts=True)

    # Lencana yang belum punya catatan rilis (dibuat sekarang, atau dibuat orang lain
    # lewat admin/form lencana). Pencatatan pertama kali dianggap sudah lama ada,
    # supaya user lama tidak dibanjiri notifikasi; selanjutnya = rilis sungguhan.
    first_run = not BadgeRelease.objects.exists()
    unrecorded = Badge.objects.filter(release__isnull=True)
    stamp = LONG_AGO if first_run else timezone.now()
    rows = [BadgeRelease(badge=b, released_at=stamp) for b in unrecorded]
    if rows:
        BadgeRelease.objects.bulk_create(rows, ignore_conflicts=True)
    return len(rows)


def award_badges(user):
    """Beri lencana yang syaratnya terpenuhi. Mengembalikan daftar Badge baru."""
    from .services import count_scans   # impor di dalam fungsi supaya tidak melingkar

    values = {
        'scan_amount': count_scans(FoodLog.objects.filter(user=user)),
        'streak_duration': game.get_profile(user).record_streak,
    }
    owned = set(UserBadge.objects.filter(user=user).values_list('badge_id', flat=True))
    earned = []
    for badge in Badge.objects.exclude(pk__in=owned):
        value = values.get(badge.criteria_type)
        if value is not None and value >= badge.threshold:
            _, created = UserBadge.objects.get_or_create(user=user, badge=badge)
            if created:
                earned.append(badge)
    return earned


def sync_badges(user):
    ensure_badges()
    return award_badges(user)

def valid_user_badges(user):
    """Lencana yang syaratnya benar-benar terpenuhi menurut aturan Challenge.

    Baris UserBadge lama dari proses Gamification tetap disimpan, tetapi lencana
    scan yang terhitung per item tidak ditampilkan sebagai didapat sebelum jumlah
    foto pengguna mencapai threshold.
    """
    from .services import count_scans

    values = {
        'scan_amount': count_scans(FoodLog.objects.filter(user=user)),
        'streak_duration': game.get_profile(user).record_streak,
    }
    valid = []
    for user_badge in (
        UserBadge.objects.filter(user=user).select_related('badge')
        .order_by('-earned_at')
    ):
        required = values.get(user_badge.badge.criteria_type)
        if required is not None and required >= user_badge.badge.threshold:
            valid.append(user_badge)
    return valid

