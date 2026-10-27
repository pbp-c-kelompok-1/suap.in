
from datetime import timedelta

from django.utils import timezone

from scanner.models import FoodLog, CarbonBudget

from gamification import services as game


DAY_ABBR = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
DEFAULT_BUDGET_GRAMS = 2000.0


def kg(grams):
    return round((grams or 0) / 1000, 2)


def week_totals_by_day(user, start_date, end_date):
    """Total emisi karbon harian dari riwayat scan pengguna."""
    logs = FoodLog.objects.filter(
        user=user,
        scanned_at__date__gte=start_date,
        scanned_at__date__lte=end_date,
    )

    totals = {}
    for log in logs:
        day = timezone.localtime(log.scanned_at).date()
        totals[day] = totals.get(day, 0) + (log.co2_grams or 0)

    return totals


def todays_quests(user, today):
    """Ambil statistik scan hari ini dari database."""
    logs = FoodLog.objects.filter(
        user=user,
        scanned_at__date=today,
    )

    scans_today = logs.count()
    used_grams = sum(log.co2_grams or 0 for log in logs)

    budget = CarbonBudget.objects.filter(
        user=user,
        date=today,
    ).first()

    budget_grams = (
        budget.budget_grams if budget else DEFAULT_BUDGET_GRAMS
    )

    # Misi belum dihubungkan ke model tersendiri.
    # Kosong lebih baik daripada menampilkan progres rekaan.
    quests = []

    return quests, scans_today, used_grams, budget_grams


def build_challenge_data(user, claimed_today=False):
    """Susun data halaman Challenge dari database yang tersedia."""
    today = timezone.localdate()
    week_start = today - timedelta(days=6)

    quests, scans_today, used_grams, budget_grams = todays_quests(
        user, today
    )

    by_day = week_totals_by_day(user, week_start, today)

    weekly = [
        {
            "d": DAY_ABBR[(week_start + timedelta(days=i)).weekday()],
            "v": kg(by_day.get(week_start + timedelta(days=i), 0)),
            "hasData": (week_start + timedelta(days=i)) in by_day,
        }
        for i in range(7)
    ]

    total_scans = FoodLog.objects.filter(user=user).count()
    from .models import ChallengeProfile
    profile = ChallengeProfile.objects.filter(user=user).first()

    game_profile = game.get_profile(user)
    prog = game.xp_progress(game_profile)

    return {
        "user": {
            "id": user.id,
            "name": (profile.display_name if profile and profile.display_name else user.username),
            "username": user.username,
            "bio": profile.bio if profile else "",
            "avatar": profile.avatar_id if profile else 0,
        },
        "game": {
            "level": game_profile.level,
            "tier": game.tier_from_level(game_profile.level),
            "xp": prog["current"],
            "cap": prog["needed"],
            "totalXp": game_profile.total_xp,
            "percent": prog["percent"],
            "streak": 0,
            "freezes": 0,
        },
        "budget": {
            "usedKg": kg(used_grams),
            "maxKg": kg(budget_grams),
        },
        "scansToday": scans_today,
        "totalScans": total_scans,
        "quests": quests,
        "chest": {
            "ready": False,
            "claimed": claimed_today,
        },
        "weekly": weekly,
        "hasWeekData": bool(by_day),
        "rank": {
            "teman": {"items": [], "empty": "no_friends"},
            "kampus": {"items": [], "empty": "no_campus"},
            "nasional": {"items": [], "empty": "no_data"},
        },
        "notifs": [],
        "stats": {
            "scans": total_scans,
            "recordStreak": 0,
            "avoidedKg": 0,
            "campusRank": None,
        },
        "badges": [],
    }
