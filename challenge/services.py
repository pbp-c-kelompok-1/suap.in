
from datetime import timedelta

from django.utils import timezone

from scanner.models import FoodLog, CarbonBudget
from gamification.models import GameProfile

from gamification import services as game

from django.contrib.auth.models import User
from django.db.models import Count, Sum
from social.models import CampusMembership


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
    """Hitung progres tiga misi harian dari data database."""
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

    over_budget = used_grams > budget_grams

    quests = [
        {
            'id': 'scan_once',
            'title': 'Scan makanan pertama',
            'desc': 'Simpan minimal satu hasil scan hari ini.',
            'val': min(scans_today, 1),
            'goal': 1,
            'tone': 'green',
            'icon': 'camera',
            'failed': False,
            'why': 'Mulai catat jejak karbon makananmu.',
        },
        {
            'id': 'scan_three',
            'title': 'Scan 3 makanan',
            'desc': 'Simpan minimal tiga hasil scan hari ini.',
            'val': min(scans_today, 3),
            'goal': 3,
            'tone': 'blue',
            'icon': 'target',
            'failed': False,
            'why': 'Kenali dampak pilihan makananmu.',
        },
        {
            'id': 'carbon_budget',
            'title': 'Jaga budget karbon',
            'desc': 'Jaga total emisi hari ini agar tidak melebihi budget.',
            'val': int(scans_today > 0 and not over_budget),
            'goal': 1,
            'tone': 'green',
            'icon': 'leaf',
            'failed': over_budget,
            'why': 'Budget karbon terlampaui.' if over_budget else 'Total emisi masih dalam budget.',
        },
    ]

    return quests, scans_today, used_grams, budget_grams


def build_rankings(user):
    # Nasional: hanya pengguna yang sudah pernah scan.
    national_users = (
        User.objects
        .annotate(scan_count=Count("food_logs"))
        .filter(scan_count__gt=0)
        .order_by("username")
    )

    national_items = [
        {
            "name": u.username,
            "scans": u.scan_count,
        }
        for u in national_users[:10]
    ]

    # Kampus: ranking pengguna yang terdaftar di kampus yang sama.
    membership = (
        CampusMembership.objects
        .filter(user=user)
        .select_related("university")
        .first()
    )

    campus_items = []
    campus_rank = None

    if membership:
        campus_users = (
            User.objects
            .filter(campus__university=membership.university)
            .annotate(total_carbon=Sum("food_logs__co2_grams"))
            .filter(total_carbon__isnull=False)
            .order_by("total_carbon", "username")
        )

        campus_rows = list(campus_users)

        campus_items = [
            {
                "name": u.username,
                "carbon": u.total_carbon or 0,
            }
            for u in campus_rows[:10]
        ]

        for position, u in enumerate(campus_rows, start=1):
            if u.pk == user.pk:
                campus_rank = position
                break

    return {
        "rank": {
            "teman": {"items": [], "empty": "no_friends"},
            "kampus": {
                "items": campus_items,
                "empty": "no_campus" if not membership else (
                    "" if campus_items else "no_data"
                ),
            },
            "nasional": {
                "items": national_items,
                "empty": "" if national_items else "no_data",
            },
        },
        "campusRank": campus_rank,
    }

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
    rank_data = build_rankings(user)

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
            "streak": game_profile.current_streak,
            "freezes": game_profile.streak_freezes,
        },
        "budget": {
            "usedKg": kg(used_grams),
            "maxKg": kg(budget_grams),
        },
        "scansToday": scans_today,
        "totalScans": total_scans,
        "quests": quests,
        "chest": {
            "ready": bool(quests) and all(
                q["val"] >= q["goal"] for q in quests
            ),
            "claimed": claimed_today,
        },
        "weekly": weekly,
        "hasWeekData": bool(by_day),
        "rank": rank_data["rank"],
        "notifs": [],
        "stats": {
            "scans": total_scans,
            "recordStreak": 0,
            "avoidedKg": 0,
            "campusRank": rank_data["campusRank"],
        },
        "badges": [],
    }
