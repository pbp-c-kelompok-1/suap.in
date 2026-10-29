
from datetime import timedelta

from django.utils import timezone

from scanner.models import FoodLog, CarbonBudget
from gamification.models import Badge, GameProfile, UserBadge

from gamification import services as game

from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.db.models.functions import TruncDate

from social.models import CampusMembership
from social.services import time_ago
from story.models import FriendChallenge
from .models import Notification, QuestClaim
from .ranking import build_rankings, build_weekly_ranking_recap


DAY_ABBR = ["Sen", "Sel", "Rab", "Kam", "Jum", "Sab", "Min"]
DEFAULT_BUDGET_GRAMS = 2000.0

# Hadiah XP tiap misi. Diklaim manual oleh user di halaman Misi.
QUEST_XP = {
    'scan_once': 10,
    'scan_three': 25,
    'carbon_budget': 20,
    'low_carbon': 20,
    'consistent_scanner': 30,
    'average_carbon': 20,
}
DEFAULT_QUEST_XP = 10

# Notifikasi
NOTIF_BADGE_WINDOW_DAYS = 14   # lencana lebih lama dari ini tidak dibuatkan notifikasi baru
NOTIF_READ_KEEP_DAYS = 30      # notifikasi yang sudah dibaca disimpan selama ini
NOTIF_TOMBSTONE_DAYS = 60      # jejak notifikasi yang dihapus user
NOTIF_MAX_SHOWN = 100


def count_scans(logs):
    """Jumlah SCAN (foto) pada queryset FoodLog, bukan jumlah item makanan.

    Satu foto disimpan sebagai beberapa baris FoodLog (satu per item), dan semua
    barisnya menyimpan respons AI yang sama. Jadi respons AI dipakai sebagai
    penanda "satu scan". Baris tanpa respons AI dihitung satu per satu.
    """
    with_raw = (
        logs.exclude(ai_raw_response='')
        .order_by().values('ai_raw_response').distinct().count()
    )
    without_raw = logs.filter(ai_raw_response='').count()
    return with_raw + without_raw


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

    scans_today = count_scans(logs)
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
    for q in quests:
        q['xp'] = QUEST_XP.get(q['id'], DEFAULT_QUEST_XP)

    return quests, scans_today, used_grams, budget_grams


def saved_budget_grams(user, today):
    """Total gram CO2 yang "dihemat" dari budget harian.

    Aturan: untuk setiap hari yang SUDAH LEWAT (hari ini tidak dihitung, karena
    belum selesai) dan punya scan, hemat = budget hari itu - total emisi hari itu.
    Hari yang melebihi budget dihitung 0, bukan minus.
    """
    rows = (
        FoodLog.objects.filter(user=user, scanned_at__date__lt=today)
        .annotate(day=TruncDate('scanned_at'))
        .order_by()
        .values('day')
        .annotate(total=Sum('co2_grams'))
    )
    budgets = dict(
        CarbonBudget.objects.filter(user=user, date__lt=today)
        .values_list('date', 'budget_grams')
    )
    saved = 0
    for row in rows:
        budget = budgets.get(row['day'], DEFAULT_BUDGET_GRAMS)
        saved += max(0, budget - (row['total'] or 0))
    return saved


def build_notifications(user, profile, scans_today, quests):
    """Kumpulkan notifikasi yang SEHARUSNYA ada sekarang.

    Hasilnya belum disimpan; persist_notifications yang menyimpannya ke database.
    """
    cands = []
    today = timezone.localdate()
    now = timezone.now()

    def add(key, kind, ico, tone, title, body, link='', ephemeral=False, created_at=None):
        cands.append({
            'key': key, 'kind': kind, 'icon': ico, 'tone': tone,
            'title': title, 'body': body, 'link': link,
            'ephemeral': ephemeral, 'created_at': created_at or now,
        })

    # Streak
    streak = game.effective_streak(profile)
    if streak > 0 and scans_today == 0:
        add(f"streak-risk-{today.isoformat()}", 'streak', 'flame', 'red',
            'Streakmu terancam hilang',
            'Belum ada foto makanan hari ini. Foto sebelum 23.59.',
            link='', ephemeral=True)
    elif streak > 0:
        add(f"streak-{today.isoformat()}-{streak}", 'streak', 'flame', 'amber',
            f'Streak {streak} hari!', 'Pertahankan terus ritmemu.')

    # Misi selesai: ajak user klaim hadiahnya
    for q in quests:
        if q['val'] >= q['goal']:
            add(f"quest-{today.isoformat()}-{q['id']}", 'misi', 'check', 'green',
                'Kamu menyelesaikan satu misi!',
                f"{q['title']} selesai. Klaim hadiahmu sekarang: +{q.get('xp', DEFAULT_QUEST_XP)} XP.",
                link='#/misi')

    if quests and all(q['val'] >= q['goal'] for q in quests):
        add(f"misi-done-{today.isoformat()}", 'misi', 'check', 'teal',
            'Semua misi hari ini selesai',
            'Buka peti bonusmu untuk dapat streak freeze.',
            link='#/misi')

    # Lencana yang baru didapat
    since = now - timedelta(days=NOTIF_BADGE_WINDOW_DAYS)
    for ub in (
        UserBadge.objects
        .filter(user=user, earned_at__gte=since)
        .select_related("badge")
        .order_by("-earned_at")[:10]
    ):
        add(f"badge-{ub.badge_id}", 'lencana', 'trophy', 'blue',
            f"Lencana baru: {ub.badge.name}",
            ub.badge.description or "Kamu membuka lencana baru.",
            link='#/profil', created_at=ub.earned_at)

    # Friend Challenge yang masih menunggu jawaban
    pending = (
        FriendChallenge.objects
        .filter(opponent=user, status="pending")
        .select_related("challenger")
        .order_by("-created_at")[:5]
    )
    for challenge in pending:
        add(f"challenge-{challenge.pk}", 'teman', 'users', 'purple',
            f"{challenge.challenger.username} menantangmu!",
            "Ada challenge baru yang menunggumu.",
            ephemeral=True, created_at=challenge.created_at)

    return cands


def persist_notifications(user, candidates):
    """Simpan notifikasi ke database lalu kembalikan daftar untuk ditampilkan.

    - Kejadian baru -> dibuat sekali (key unik), tidak dobel.
    - Status baca & hapus ada di database, jadi tidak hilang saat pindah perangkat.
    - Notifikasi "sementara" (ephemeral) dihapus otomatis kalau sudah tidak relevan.
    - Notifikasi yang sudah dibaca disimpan NOTIF_READ_KEEP_DAYS hari sebagai riwayat.
    """
    now = timezone.now()
    current_keys = {c['key'] for c in candidates}
    existing = {n.key: n for n in Notification.objects.filter(user=user)}

    stale = [n.pk for n in existing.values() if n.ephemeral and n.key not in current_keys]
    if stale:
        Notification.objects.filter(pk__in=stale).delete()
        existing = {k: n for k, n in existing.items() if n.pk not in stale}

    fresh = [
        Notification(
            user=user, key=c['key'], kind=c['kind'], icon=c['icon'], tone=c['tone'],
            title=c['title'], body=c['body'], link=c['link'],
            ephemeral=c['ephemeral'], created_at=c['created_at'],
        )
        for c in candidates if c['key'] not in existing
    ]
    if fresh:
        Notification.objects.bulk_create(fresh, ignore_conflicts=True)

    Notification.objects.filter(
        user=user, read_at__lt=now - timedelta(days=NOTIF_READ_KEEP_DAYS),
    ).delete()
    Notification.objects.filter(
        user=user, dismissed=True, created_at__lt=now - timedelta(days=NOTIF_TOMBSTONE_DAYS),
    ).delete()

    rows = (
        Notification.objects.filter(user=user, dismissed=False)
        .order_by('-created_at', '-id')[:NOTIF_MAX_SHOWN]
    )
    return [serialize_notification(n) for n in rows]


def serialize_notification(n):
    return {
        "id": n.key,
        "type": n.kind,
        "ico": n.icon,
        "tone": n.tone,
        "t": n.title,
        "p": n.body,
        "time": time_ago(n.created_at),
        "read": n.read_at is not None,
        "link": n.link,
    }


def build_challenge_data(user, claimed_today=False):
    """Susun data halaman Challenge dari database yang tersedia."""
    today = timezone.localdate()
    # Satu minggu = Senin sampai Minggu (sama dengan peringkat mingguan),
    # jadi rentang tanggalnya tetap sepanjang minggu dan baru berganti hari Senin.
    week_start = today - timedelta(days=today.weekday())
    week_end = week_start + timedelta(days=6)

    quests, scans_today, used_grams, budget_grams = todays_quests(
        user, today
    )

    claimed_ids = set(
        QuestClaim.objects.filter(user=user, date=today)
        .values_list('quest_id', flat=True)
    )
    for q in quests:
        q['claimed'] = q['id'] in claimed_ids

    by_day = week_totals_by_day(user, week_start, today)

    weekly = []
    for i in range(7):
        day = week_start + timedelta(days=i)
        weekly.append({
            "d": DAY_ABBR[i],
            "v": kg(by_day.get(day, 0)),
            "hasData": day in by_day,
            "future": day > today,
            "today": day == today,
        })

    user_logs = FoodLog.objects.filter(user=user)
    total_scans = count_scans(user_logs)
    from .models import ChallengeProfile
    profile = ChallengeProfile.objects.filter(user=user).first()

    game_profile = game.get_profile(user)
    prog = game.xp_progress(game_profile)
    rank_data = build_rankings(user)
    weekly_ranking = build_weekly_ranking_recap(user)   

    # Selisih budget di hari-hari yang sudah lewat (hari ini belum dihitung)
    below_budget_grams = saved_budget_grams(user, today)
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
        "weekRange": {"start": week_start.isoformat(), "end": week_end.isoformat()},
        "hasWeekData": bool(by_day),
        "weeklyRanking": weekly_ranking,
        "rank": rank_data["rank"],
        "userTotalCarbon": rank_data["userTotalCarbon"],    
        "notifs": persist_notifications(
            user,
            build_notifications(user, game_profile, scans_today, quests),
        ),
        "stats": {
            "scans": total_scans,
            "recordStreak": game_profile.record_streak,
            "avoidedKg": kg(below_budget_grams),
            "campusRank": rank_data["campusRank"],
        },
        "badges": badges,
    }
