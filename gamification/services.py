from datetime import timedelta

from django.db import transaction
from django.utils import timezone

from scanner.models import FoodLog
from .models import Badge, GameProfile, UserBadge

MAX_LEVEL = 50
# Level + 1 = BASE_XP + STEP_XP * Current Level
BASE_XP = 50
STEP_XP = 10
# Streak Freezes
MAX_STORED_FREEZES = 2
MAX_CLAIMS_PER_WEEK = 2

TIERS = [
    (1, 'Pemula Sadar'),
    (10, 'Pejuang Hijau'),
    (20, 'Guardian Bumi'),
    (35, 'Legenda Lestari'),
]


# ==== Level dan pangkat ============================================

def xp_needed(level):
    return BASE_XP + STEP_XP * level

def xp_floor(level):
    return sum(xp_needed(k) for k in range(1, level))

def level_from_xp(total_xp):
    level, remaining = 1, total_xp
    while level < MAX_LEVEL and remaining >= xp_needed(level):
        remaining -= xp_needed(level)
        level += 1
    return level

def tier_from_level(level):
    return [name for min_level, name in TIERS if level >= min_level][-1]

def next_tier(level):
    return next(((lv, name) for lv, name in TIERS if lv > level), None)

def xp_progress(profile):
    if profile.level >= MAX_LEVEL:
        return {'current': 0, 'needed': 0, 'percent': 100}
    current = profile.total_xp - xp_floor(profile.level)
    needed = xp_needed(profile.level)
    return {'current': current, 'needed': needed, 'percent': min(100, round(current / needed * 100))}

def award_xp(user, amount):
    with transaction.atomic():
        profile = _locked_profile(user)
        old_level = profile.level
        profile.total_xp += max(0, int(amount))
        profile.level = level_from_xp(profile.total_xp)
        profile.save(update_fields=['total_xp', 'level'])
    return {
        'xp_gained': amount,
        'level': profile.level,
        'leveled_up': profile.level > old_level,
        'tier_changed': tier_from_level(profile.level) != tier_from_level(old_level),
    }


# ==== Profile ==================================================

def get_profile(user):
    return GameProfile.objects.get_or_create(user=user)[0]


def _locked_profile(user):
    return GameProfile.objects.select_for_update().get_or_create(user=user)[0]

# ==== Streak ====================================================

def update_streak(user, today=None):
    # Panggil tiap simpen scan
    today = today or timezone.localdate()
    with transaction.atomic():
        profile = _locked_profile(user)
        last = profile.last_activity_date
        if last == today:
            return profile

        if last is None:
            profile.current_streak = 1
        else:
            missed = (today - last).days - 1
            if missed <= 0:
                profile.current_streak += 1
            elif profile.streak_freezes >= missed:
                profile.streak_freezes -= missed
                # Hari yang ditutup freeze ikut dihitung, supaya halaman streak
                # bisa menurunkan hari freeze tanpa tabel tambahan.
                profile.current_streak += missed + 1
            else:
                profile.current_streak = 1

        profile.record_streak = max(profile.record_streak, profile.current_streak)
        profile.last_activity_date = today
        profile.save()
    return profile


def effective_streak(profile, today=None):
    # Streak yang ditampilkan, 0 kalo udah putus tapi belum direset di database
    today = today or timezone.localdate()
    if not profile.last_activity_date:
        return 0
    missed = (today - profile.last_activity_date).days - 1
    if missed <= 0 or profile.streak_freezes >= missed:
        return profile.current_streak
    return 0


def claim_streak_freeze(user, today=None):
    # return (boolean, string pesan jika gagal)
    today = today or timezone.localdate()
    week_start = today - timedelta(days=today.weekday())
    with transaction.atomic():
        profile = _locked_profile(user)
        if profile.freeze_week_start != week_start:
            profile.freeze_week_start = week_start
            profile.freezes_claimed_this_week = 0
        if profile.freezes_claimed_this_week >= MAX_CLAIMS_PER_WEEK:
            return False, 'Batas klaim freeze minggu ini sudah habis.'
        if profile.streak_freezes >= MAX_STORED_FREEZES:
            return False, 'Kamu sudah menyimpan freeze maksimal.'
        profile.streak_freezes += 1
        profile.freezes_claimed_this_week += 1
        profile.save()
    return True, ''


# ==== Badge/Lencana ====================================================================

def check_badges(user):
    profile = get_profile(user)
    values = {
        'scan_amount': FoodLog.objects.filter(user=user).count(),
        'streak_duration': profile.record_streak,
        # Bisa tambahin kriteria badge lain
    }
    owned = UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    new_badges = []
    for badge in Badge.objects.exclude(id__in=owned):
        if values.get(badge.criteria_type, 0) >= badge.threshold:
            _, created = UserBadge.objects.get_or_create(user=user, badge=badge)
            if created:
                new_badges.append(badge)
    return new_badges


# ==== Scanner ==========================================================================

def record_scan(user, xp):
    profile = update_streak(user)
    result = award_xp(user, xp)
    result['streak'] = profile.current_streak
    result['new_badges'] = check_badges(user)
    return result