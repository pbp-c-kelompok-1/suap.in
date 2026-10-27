
from datetime import timedelta

from django.utils import timezone

from scanner.models import FoodLog, CarbonBudget
from gamification.models import Badge, GameProfile, UserBadge

from gamification import services as game

from django.contrib.auth.models import User
from django.db.models import Count, Sum

from social.models import CampusMembership
from social.services import time_ago
from story.models import FriendChallenge


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

    # Data kebiasaan user untuk menentukan variasi misi.
    recent_start = today - timedelta(days=6)
    recent_logs = FoodLog.objects.filter(
        user=user,
        scanned_at__date__gte=recent_start,
        scanned_at__date__lt=today,
    )

    recent_scan_days = set()
    recent_grams = 0

    for log in recent_logs:
        recent_scan_days.add(
            timezone.localtime(log.scanned_at).date()
        )
        recent_grams += log.co2_grams or 0

    # Seed dibuat dari user + tanggal supaya misi tetap sama
    # selama satu hari, tetapi bisa berubah di hari berikutnya.
    import random

    rng = random.Random(
        f"{user.pk}-{today.isoformat()}"
    )

    quest_pool = []

    # Misi scan tetap tersedia, tetapi tidak selalu semuanya dipilih.
    quest_pool.append({
        'id': 'scan_once',
        'title': 'Scan makanan pertama',
        'desc': 'Simpan minimal satu hasil scan hari ini.',
        'val': min(scans_today, 1),
        'goal': 1,
        'tone': 'green',
        'icon': 'camera',
        'failed': False,
        'why': 'Mulai catat jejak karbon makananmu.',
    })

    quest_pool.append({
        'id': 'scan_three',
        'title': 'Scan 3 makanan',
        'desc': 'Simpan minimal tiga hasil scan hari ini.',
        'val': min(scans_today, 3),
        'goal': 3,
        'tone': 'blue',
        'icon': 'target',
        'failed': False,
        'why': 'Kenali dampak pilihan makananmu.',
    })

    # Misi berdasarkan jumlah CO2 hari ini.
    quest_pool.append({
        'id': 'carbon_budget',
        'title': 'Jaga budget karbon',
        'desc': 'Jaga total emisi hari ini agar tidak melebihi budget.',
        'val': int(scans_today > 0 and not over_budget),
        'goal': 1,
        'tone': 'green',
        'icon': 'leaf',
        'failed': over_budget,
        'why': (
            'Budget karbon terlampaui.'
            if over_budget
            else 'Total emisi masih dalam budget.'
        ),
    })

    # Misi untuk menjaga emisi tetap rendah.
    low_carbon_goal = 500

    quest_pool.append({
        'id': 'low_carbon',
        'title': 'Pilih makanan rendah karbon',
        'desc': f'Jaga total emisi hari ini di bawah {low_carbon_goal}g CO2.',
        'val': int(
            scans_today > 0
            and used_grams <= low_carbon_goal
        ),
        'goal': 1,
        'tone': 'green',
        'icon': 'leaf',
        'failed': used_grams > low_carbon_goal,
        'why': 'Coba pilih makanan dengan jejak karbon lebih rendah.',
    })

    # Misi menjaga konsistensi selama beberapa hari.
    active_days_goal = 3

    quest_pool.append({
        'id': 'consistent_scanner',
        'title': 'Tetap konsisten',
        'desc': f'Scan makanan setidaknya {active_days_goal} hari minggu ini.',
        'val': min(
            len(recent_scan_days) + (1 if scans_today > 0 else 0),
            active_days_goal,
        ),
        'goal': active_days_goal,
        'tone': 'blue',
        'icon': 'target',
        'failed': False,
        'why': 'Kebiasaan kecil yang konsisten lebih mudah dipertahankan.',
    })

    # Misi mengurangi rata-rata emisi dibanding minggu berjalan.
    if recent_scan_days:
        average_goal = 400

        quest_pool.append({
            'id': 'average_carbon',
            'title': 'Jaga rata-rata emisi',
            'desc': f'Usahakan rata-rata scan di bawah {average_goal}g CO2.',
            'val': int(
                scans_today > 0
                and (used_grams / scans_today) <= average_goal
            ),
            'goal': 1,
            'tone': 'teal',
            'icon': 'leaf',
            'failed': (
                scans_today > 0
                and (used_grams / scans_today) > average_goal
            ),
            'why': 'Bandingkan pilihan makananmu dan coba turunkan emisinya.',
        })

    # Acak pilihan berdasarkan user dan tanggal.
    rng.shuffle(quest_pool)

    # Ambil maksimal tiga misi.
    quests = quest_pool[:3]

    return quests, scans_today, used_grams, budget_grams


def build_rankings(user):
    # Nasional: semua user yang sudah terdaftar.
    # User tanpa scan tetap ditampilkan dengan nilai 0.
    national_users = (
        User.objects
        .annotate(
            total_carbon=Sum("food_logs__co2_grams"),
            scan_count=Count("food_logs"),
        )
        .order_by("total_carbon", "username")
    )

    national_items = [
        {
            "name": u.username,
            "scans": u.scan_count,
            "carbon": u.total_carbon or 0,
            "kg": round((u.total_carbon or 0) / 1000, 2),
            "pos": i,
            "is_me": u.pk == user.pk,
        }
        for i, u in enumerate(national_users[:10], start=1)
    ]

    # Kampus: user yang terdaftar di kampus yang sama.
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
            .annotate(
                total_carbon=Sum("food_logs__co2_grams"),
                scan_count=Count("food_logs"),
            )
            .order_by("total_carbon", "username")
        )

        campus_rows = list(campus_users)

        campus_items = [
            {
                "name": u.username,
                "scans": u.scan_count,
                "carbon": u.total_carbon or 0,
                "kg": round((u.total_carbon or 0) / 1000, 2),
                "pos": i,
                "is_me": u.pk == user.pk,
            }
            for i, u in enumerate(campus_rows[:10], start=1)
        ]

        for position, u in enumerate(campus_rows, start=1):
            if u.pk == user.pk:
                campus_rank = position
                break

    return {
        "rank": {
            "teman": {
                "items": [],
                "empty": "no_friends",
            },
            "kampus": {
                "items": campus_items,
                "empty": "no_campus" if not membership else (
                    "" if campus_items else "no_data"
                ),
            },
            "nasional": {
                "items": national_items,
                "empty": "",
            },
        },
        "campusRank": campus_rank,
    }

def build_notifications(user, profile, scans_today, all_quests_done):
    """Bangun notifikasi dari data server yang memang sudah ada."""
    notifs = []
    today = timezone.localdate()

    # Streak
    streak = game.effective_streak(profile)

    if streak > 0 and scans_today == 0:
        notifs.append({
            "id": f"streak-risk-{today.isoformat()}",
            "type": "streak",
            "ico": "flame",
            "tone": "red",
            "t": "Streakmu terancam hilang",
            "p": "Belum ada foto makanan hari ini. Foto sebelum 23.59.",
            "time": "Hari ini",
        })
    elif streak > 0:
        notifs.append({
            "id": f"streak-{today.isoformat()}-{streak}",
            "type": "streak",
            "ico": "flame",
            "tone": "amber",
            "t": f"Streak {streak} hari!",
            "p": "Pertahankan terus ritmemu.",
            "time": "Hari ini",
        })

    # Semua misi selesai
    if all_quests_done:
        notifs.append({
            "id": f"misi-done-{today.isoformat()}",
            "type": "misi",
            "ico": "check",
            "tone": "teal",
            "t": "Semua misi hari ini selesai",
            "p": "Buka peti bonusmu untuk dapat streak freeze.",
            "time": "Hari ini",
        })

    # Lencana yang sudah benar-benar dimiliki user
    for ub in (
        UserBadge.objects
        .filter(user=user)
        .select_related("badge")
        .order_by("-earned_at")[:5]
    ):
        notifs.append({
            "id": f"badge-{ub.badge_id}",
            "type": "lencana",
            "ico": "trophy",
            "tone": "blue",
            "t": f"Lencana baru: {ub.badge.name}",
            "p": ub.badge.description or "Kamu membuka lencana baru.",
            "time": time_ago(ub.earned_at),
        })

    # Friend Challenge yang masih pending
    pending = (
        FriendChallenge.objects
        .filter(opponent=user, status="pending")
        .select_related("challenger")
        .order_by("-created_at")[:5]
    )

    for challenge in pending:
        challenger_name = challenge.challenger.username

        notifs.append({
            "id": f"challenge-{challenge.pk}",
            "type": "teman",
            "ico": "users",
            "tone": "purple",
            "t": f"{challenger_name} menantangmu!",
            "p": "Ada challenge baru yang menunggumu.",
            "time": time_ago(challenge.created_at),
        })

    return notifs

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

    user_logs = FoodLog.objects.filter(user=user)
    total_scans = user_logs.count()
    from .models import ChallengeProfile
    profile = ChallengeProfile.objects.filter(user=user).first()

    game_profile = game.get_profile(user)
    prog = game.xp_progress(game_profile)
    rank_data = build_rankings(user)

    # Tampilkan statistik profil dari data tersimpan
    budget_rows = CarbonBudget.objects.filter(user=user, used_grams__gt=0)
    below_budget_grams = sum(
        max(0, row.budget_grams - row.used_grams)
        for row in budget_rows
    )
    earned_badge_ids = set(
        UserBadge.objects.filter(user=user).values_list('badge_id', flat=True)
    )
    badges = [
        {
            'id': badge.id,
            'name': badge.name,
            'type': badge.criteria_type,
            'desc': badge.description,
            'earned': badge.id in earned_badge_ids,
        }
        for badge in Badge.objects.all().order_by('criteria_type', 'threshold', 'name')
    ]

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
        "notifs": build_notifications(
            user,
            game_profile,
            scans_today,
            all_quests_done=all(
                q["val"] >= q["goal"] for q in quests
            ),
        ),
        "stats": {
            "scans": total_scans,
            "recordStreak": game_profile.record_streak,
            "avoidedKg": kg(below_budget_grams),
            "campusRank": rank_data["campusRank"],
        },
        "badges": badges,
    }
