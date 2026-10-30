
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
from django.urls import reverse

from .models import ChallengeProfile, DailyQuestSet, Notification, QuestClaim
from .ranking import compute_leaderboard


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
    'scan_two': 15,
    'scan_four': 35,
    'beat_yesterday': 25,
    'light_item': 15,
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



# ---- Misi harian ------------------------------------------------------------
#
# Misi dipilih dari katalog di bawah. Pilihannya:
# - beda tiap user (seed memakai id user) dan beda tiap hari (seed memakai tanggal),
# - dipengaruhi kebiasaan 6 hari terakhir (lihat _habit_weights),
# - tidak boleh sama dengan misi kemarin,
# - disimpan di DailyQuestSet, jadi tidak berubah-ubah sepanjang hari.
QUESTS_PER_DAY = 3
FAMILY_CAP = {'count': 1, 'carbon': 2, 'habit': 1}   # batas misi sejenis per hari
QUEST_FAMILY = {
    'scan_once': 'count', 'scan_two': 'count', 'scan_three': 'count', 'scan_four': 'count',
    'carbon_budget': 'carbon', 'low_carbon': 'carbon', 'average_carbon': 'carbon',
    'beat_yesterday': 'carbon', 'light_item': 'carbon',
    'consistent_scanner': 'habit',
}


def _round_to(value, step, lo, hi):
    return int(max(lo, min(hi, round(value / step) * step)))


def _day_stats(logs):
    """{tanggal: {'grams': total, 'scans': jumlah scan}} dari queryset FoodLog."""
    days = {}
    for log in logs:
        day = timezone.localtime(log.scanned_at).date()
        d = days.setdefault(day, {'grams': 0, 'raws': set(), 'loose': 0})
        d['grams'] += log.co2_grams or 0
        if log.ai_raw_response:
            d['raws'].add(log.ai_raw_response)
        else:
            d['loose'] += 1
    return {
        day: {'grams': d['grams'], 'scans': len(d['raws']) + d['loose']}
        for day, d in days.items()
    }


def _quest_context(user, today):
    logs = FoodLog.objects.filter(user=user, scanned_at__date=today)
    scans_today = count_scans(logs)
    used_grams = sum(log.co2_grams or 0 for log in logs)
    lightest = min((log.co2_grams or 0 for log in logs), default=None)

    budget = CarbonBudget.objects.filter(user=user, date=today).first()
    budget_grams = budget.budget_grams if budget else DEFAULT_BUDGET_GRAMS

    # Kebiasaan: 6 hari sebelum hari ini.
    recent = _day_stats(FoodLog.objects.filter(
        user=user,
        scanned_at__date__gte=today - timedelta(days=6),
        scanned_at__date__lt=today,
    ))
    n_days = len(recent)
    total_g = sum(d['grams'] for d in recent.values())
    total_scans = sum(d['scans'] for d in recent.values())
    yesterday = recent.get(today - timedelta(days=1))
    return {
        'scans_today': scans_today,
        'used_grams': used_grams,
        'lightest': lightest,
        'budget_grams': budget_grams,
        'over_budget': used_grams > budget_grams,
        'recent_days': n_days,
        'avg_day_g': (total_g / n_days) if n_days else None,
        'avg_scan_g': (total_g / total_scans) if total_scans else None,
        'avg_scans_per_day': (total_scans / n_days) if n_days else None,
        'yesterday_g': yesterday['grams'] if yesterday else None,
    }


def _quest_catalog(c):
    """Semua misi yang BISA muncul untuk user ini hari ini, lengkap dengan progresnya."""
    st, used = c['scans_today'], c['used_grams']
    cat = {}

    def add(qid, **q):
        q.setdefault('failed', False)
        q['id'] = qid
        cat[qid] = q

    for qid, goal, title, why in (
        ('scan_once', 1, 'Scan makanan pertama', 'Mulai catat jejak karbon makananmu.'),
        ('scan_two', 2, 'Scan 2 makanan', 'Dua scan sehari bikin gambaran harianmu lebih lengkap.'),
        ('scan_three', 3, 'Scan 3 makanan', 'Kenali dampak pilihan makananmu.'),
    ):
        add(qid, title=title, why=why, goal=goal, val=min(st, goal), tone='green' if goal == 1 else 'blue',
            icon='camera' if goal == 1 else 'target',
            desc=f'Simpan minimal {goal} hasil scan hari ini.')
    if (c['avg_scans_per_day'] or 0) >= 2.5:
        add('scan_four', title='Scan 4 makanan', why='Kamu sudah rajin scan, naikkan sedikit tantangannya.',
            goal=4, val=min(st, 4), tone='blue', icon='target',
            desc='Simpan minimal 4 hasil scan hari ini.')

    add('carbon_budget', title='Jaga budget karbon', why=('Budget karbon terlampaui.' if c['over_budget'] else 'Total emisi masih dalam budget.'),
        desc='Jaga total emisi hari ini agar tidak melebihi budget.', goal=1,
        val=int(st > 0 and not c['over_budget']), failed=c['over_budget'], tone='green', icon='leaf')

    # Target rendah karbon mengikuti kebiasaan: sedikit di bawah rata-rata harianmu.
    low_goal = _round_to(c['avg_day_g'] * 0.85, 50, 400, 1500) if c['avg_day_g'] else 800
    add('low_carbon', title='Pilih makanan rendah karbon',
        desc=f'Jaga total emisi hari ini di bawah {low_goal}g CO2.', goal=1,
        val=int(st > 0 and used <= low_goal), failed=used > low_goal, tone='green', icon='leaf',
        why='Coba pilih makanan dengan jejak karbon lebih rendah.')

    add('light_item', title='Satu pilihan ringan',
        desc='Catat satu makanan di bawah 150g CO2 hari ini.', goal=1,
        val=int(c['lightest'] is not None and c['lightest'] <= 150), tone='teal', icon='leaf',
        why='Satu pilihan kecil yang ringan sudah menghitung.')

    if c['recent_days']:
        avg_goal = _round_to(c['avg_scan_g'] * 0.9, 50, 250, 600) if c['avg_scan_g'] else 400
        per_scan = (used / st) if st else None
        add('average_carbon', title='Jaga rata-rata emisi',
            desc=f'Usahakan rata-rata scan di bawah {avg_goal}g CO2.', goal=1,
            val=int(per_scan is not None and per_scan <= avg_goal),
            failed=per_scan is not None and per_scan > avg_goal, tone='teal', icon='leaf',
            why='Bandingkan pilihan makananmu dan coba turunkan emisinya.')

        days_goal = 3 if c['recent_days'] < 4 else 4
        add('consistent_scanner', title='Tetap konsisten',
            desc=f'Scan makanan setidaknya {days_goal} hari dalam seminggu ini.', goal=days_goal,
            val=min(c['recent_days'] + (1 if st > 0 else 0), days_goal), tone='blue', icon='target',
            why='Kebiasaan kecil yang konsisten lebih mudah dipertahankan.')

    if c['yesterday_g']:
        add('beat_yesterday', title='Lebih ringan dari kemarin',
            desc='Total emisi hari ini lebih rendah dari kemarin.', goal=1,
            val=int(st > 0 and used < c['yesterday_g']), failed=used >= c['yesterday_g'] and st > 0,
            tone='teal', icon='leaf', why='Kemarin ' + f"{round(c['yesterday_g'])}g CO2. Bisa lebih rendah hari ini?")
    return cat


def _habit_weights(catalog, c):
    """Bobot pemilihan per misi, disesuaikan dengan kebiasaan user."""
    w = {qid: 1.0 for qid in catalog}

    def boost(ids, factor):
        for qid in ids:
            if qid in w:
                w[qid] *= factor

    if c['recent_days'] <= 1:                        # jarang scan -> ajak mulai & konsisten
        boost(('scan_once', 'scan_two', 'consistent_scanner', 'light_item'), 2.0)
    if c['recent_days'] >= 4:                        # rajin -> tantangan lebih
        boost(('consistent_scanner', 'beat_yesterday', 'average_carbon'), 1.6)
    avg_scans = c['avg_scans_per_day']
    if avg_scans is not None:
        if avg_scans >= 2.5:
            boost(('scan_four', 'scan_three'), 1.8)
        elif avg_scans <= 1.5:
            boost(('scan_once', 'scan_two'), 1.5)
            boost(('scan_three',), 0.6)
    if c['avg_day_g'] is not None and c['avg_day_g'] > c['budget_grams']:
        boost(('low_carbon', 'carbon_budget', 'average_carbon', 'light_item'), 2.0)   # sering lewat budget
    return w


def _pick_quest_ids(user, today, catalog, c, avoid):
    import random
    rng = random.Random(f"{user.pk}-{today.isoformat()}")
    weights = _habit_weights(catalog, c)
    candidates = [q for q in catalog if q not in avoid]
    if len(candidates) < QUESTS_PER_DAY:            # katalog terlalu kecil: abaikan larangan
        candidates = list(catalog)

    picked, used_family = [], {}
    pool = list(candidates)
    while pool and len(picked) < QUESTS_PER_DAY:
        total = sum(weights[q] for q in pool)
        r, acc, choice = rng.uniform(0, total), 0.0, pool[-1]
        for q in pool:
            acc += weights[q]
            if r <= acc:
                choice = q
                break
        pool.remove(choice)
        fam = QUEST_FAMILY.get(choice, choice)
        if used_family.get(fam, 0) >= FAMILY_CAP.get(fam, 1):
            continue
        used_family[fam] = used_family.get(fam, 0) + 1
        picked.append(choice)
    # Kalau batas keluarga bikin kurang dari 3, isi sisanya tanpa batas.
    for q in candidates:
        if len(picked) >= QUESTS_PER_DAY:
            break
        if q not in picked:
            picked.append(q)
    return picked


def todays_quests(user, today):
    c = _quest_context(user, today)
    catalog = _quest_catalog(c)

    stored = DailyQuestSet.objects.filter(user=user, date=today).first()
    ids = [q for q in stored.ids() if q in catalog] if stored else []
    if len(ids) < QUESTS_PER_DAY:
        prev = DailyQuestSet.objects.filter(user=user, date=today - timedelta(days=1)).first()
        ids = _pick_quest_ids(user, today, catalog, c, set(prev.ids()) if prev else set())
        DailyQuestSet.objects.update_or_create(
            user=user, date=today, defaults={'quest_ids': ','.join(ids)},
        )

    quests = []
    for qid in ids:
        q = dict(catalog[qid])
        q['xp'] = QUEST_XP.get(qid, DEFAULT_QUEST_XP)
        quests.append(q)
    return quests, c['scans_today'], c['used_grams'], c['budget_grams']


def saved_budget_grams(user, today):
    """Total gram CO2 yang "dihemat" dari budget harian.

    Aturan: untuk setiap hari yang punya scan, hemat = budget hari itu - total
    emisi hari itu. Hari yang melebihi budget dihitung 0, bukan minus.

    Hari ini IKUT dihitung secara sementara: angkanya mengikuti total emisi hari
    ini sampai sekarang, jadi turun kalau user scan lagi dan jadi 0 begitu
    melewati budget harian. Besok angkanya sudah final.
    """
    rows = (
        FoodLog.objects.filter(user=user, scanned_at__date__lte=today)
        .annotate(day=TruncDate('scanned_at'))
        .order_by()
        .values('day')
        .annotate(total=Sum('co2_grams'))
    )
    budgets = dict(
        CarbonBudget.objects.filter(user=user, date__lte=today)
        .values_list('date', 'budget_grams')
    )
    saved = 0
    for row in rows:
        budget = budgets.get(row['day'], DEFAULT_BUDGET_GRAMS)
        saved += max(0, budget - (row['total'] or 0))
    return saved


def saved_today_grams(user, today):
    """Gram CO2 yang dihemat dari budget HARI INI saja.

    hemat = budget hari ini - total emisi hari ini, minimal 0 (lewat budget -> 0).
    Selalu mengikuti scan terbaru, dan mulai dari 0 lagi setiap ganti hari.
    """
    used = (
        FoodLog.objects.filter(user=user, scanned_at__date=today)
        .aggregate(total=Sum('co2_grams'))['total']
    )
    if used is None:      # belum ada scan hari ini
        return 0
    row = CarbonBudget.objects.filter(user=user, date=today).first()
    budget = row.budget_grams if row else DEFAULT_BUDGET_GRAMS
    return max(0, budget - used)


def build_notifications(user, profile, scans_today, quests, extra=None):
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
    elif profile.current_streak > 0 and profile.last_activity_date:
        # Streak sudah putus tapi belum direset di database (user belum scan lagi).
        add(f"streak-lost-{profile.last_activity_date.isoformat()}", 'streak', 'flame', 'red',
            'Streakmu terputus',
            f'Streak {profile.current_streak} harimu berakhir. Scan hari ini untuk mulai lagi!',
            link='', created_at=now)

    # Misi baru hari ini
    if quests:
        add(f"quests-new-{today.isoformat()}", 'misi', 'target', 'blue',
            f'Kamu punya {len(quests)} misi baru hari ini!',
            'Selesaikan semuanya untuk membuka peti bonus.',
            link='#/misi')

    # Misi selesai: ajak user klaim hadiahnya
    for q in quests:
        if q['val'] >= q['goal']:
            add(f"quest-{today.isoformat()}-{q['id']}", 'misi', 'check', 'green',
                'Kamu menyelesaikan satu misi!',
                f"{q['title']} selesai. Klaim hadiahmu sekarang: +{q.get('xp', DEFAULT_QUEST_XP)} XP.",
                link='#/misi')

    if quests and all(q['val'] >= q['goal'] for q in quests):
        add(f"misi-done-{today.isoformat()}", 'misi', 'check', 'teal',
            'Kamu sudah menyelesaikan semua misi hari ini!',
            'Klaim peti bonusmu, lalu kembali besok untuk misi baru.',
            link='#/misi')

    # Lencana yang baru didapat
    since = now - timedelta(days=NOTIF_BADGE_WINDOW_DAYS)
    earned_ids = set()
    for ub in (
        UserBadge.objects
        .filter(user=user)
        .select_related("badge")
        .order_by("-earned_at")
    ):
        earned_ids.add(ub.badge_id)
        if ub.earned_at >= since and len([c for c in cands if c['kind'] == 'lencana']) < 10:
            add(f"badge-{ub.badge_id}", 'lencana', 'trophy', 'blue',
                f"Lencana baru: {ub.badge.name}",
                ub.badge.description or "Kamu membuka lencana baru.",
                link='#/profil', created_at=ub.earned_at)

    # Pengumuman lencana yang baru dirilis hanya bisa dihitung bila model Badge
    # memiliki timestamp rilis. Branch Challenge tidak menambah field lintas-app;
    # bila field belum ada, lewati bagian ini tanpa membuat dashboard error.
    if any(field.name == 'created_at' for field in Badge._meta.get_fields()):
        released_after = max(since, user.date_joined)
        for badge in Badge.objects.filter(created_at__gte=released_after).order_by('-created_at'):
            if badge.id in earned_ids:
                continue
            add(f"badge-new-{badge.id}", 'lencana', 'star', 'amber',
                f"Lencana baru dirilis: {badge.name}",
                f"{badge.description or 'Ada lencana baru.'} Yuk kejar!",
                link='#/profil', created_at=badge.created_at)

    # Friend Challenge yang masih menunggu jawaban
    pending = list(
        FriendChallenge.objects
        .filter(opponent=user, status="pending")
        .select_related("challenger")
        .order_by("-created_at")[:5]
    )
    names = {
        p.user_id: p.display_name
        for p in ChallengeProfile.objects.filter(user_id__in=[c.challenger_id for c in pending])
        if p.display_name
    }
    for challenge in pending:
        who = names.get(challenge.challenger_id) or challenge.challenger.username
        add(f"challenge-{challenge.pk}", 'teman', 'sword', 'purple',
            f"{who} menantangmu!",
            f"Adu {challenge.get_metric_display().lower()} selama {challenge.duration_days} hari.",
            link=reverse('story:challenge_list'),
            ephemeral=True, created_at=challenge.created_at)

    # Kejadian lain yang dihitung di luar (mis. perubahan peringkat)
    for ev in (extra or []):
        add(**ev)

    return cands


def rank_notifications(user, rank_data, today=None):
    """Notifikasi saat peringkat nasional minggu ini naik atau turun.

    Posisi terakhir yang sudah dilihat user disimpan di ChallengeProfile, jadi
    tiap perubahan hanya diberitahukan satu kali. Pengecekan terjadi tiap user
    membuka dashboard, karena peringkat berubah juga akibat scan orang lain.
    """
    today = today or timezone.localdate()
    week = today - timedelta(days=today.weekday())
    nat = rank_data['rank']['nasional']
    pos, total = nat['position'], nat['total']
    prof, _ = ChallengeProfile.objects.get_or_create(user=user)
    same_week = prof.last_rank_week == week
    old = prof.last_rank if same_week else None
    if pos is None:
        # Simpan bahwa dashboard sudah dibuka sebelum pengguna memenuhi syarat
        # peringkat, agar saat ia masuk leaderboard notifikasinya spesifik.
        if not same_week or prof.last_rank is None:
            prof.last_rank = 0
            prof.last_rank_week = week
            prof.save(update_fields=['last_rank', 'last_rank_week'])
        return []
    stamp = timezone.now().strftime('%Y%m%d%H%M%S')
    events = []
    if old is None or old == 0:
        first_title = (f"Kamu masuk leaderboard minggu ini: #{pos}" if old == 0
                       else f"Kamu masuk peringkat minggu ini: #{pos}")
        events.append(dict(
            key=f"rank-first-{week.isoformat()}", kind='peringkat', ico='trophy', tone='teal',
            title=first_title,
            body=f"Dari {total} pengguna. Pertahankan pilihan rendah karbonmu!", link='#/laporan'))
    elif pos < old:
        events.append(dict(
            key=f"rank-{stamp}-{old}-{pos}", kind='peringkat', ico='trophy', tone='green',
            title=f"Kamu naik ke peringkat #{pos}!",
            body=f"Sebelumnya #{old}, dari {total} pengguna minggu ini.", link='#/laporan'))
    elif pos > old:
        events.append(dict(
            key=f"rank-{stamp}-{old}-{pos}", kind='peringkat', ico='alert', tone='amber',
            title=f"Peringkatmu turun ke #{pos}",
            body=f"Sebelumnya #{old}, dari {total} pengguna. Yuk kejar lagi dengan menu rendah karbon!",
            link='#/laporan'))
    if (prof.last_rank, prof.last_rank_week) != (pos, week):
        prof.last_rank, prof.last_rank_week = pos, week
        prof.save(update_fields=['last_rank', 'last_rank_week'])
    return events


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
    # Pastikan katalog lencana ada dan lencana yang sudah memenuhi syarat tercatat.
    game.check_badges(user)
    board = compute_leaderboard(user, today)      # satu kali hitung untuk semua bagian
    rank_data = board
    weekly_ranking = board['recap']

    # Hemat dari budget: hari ini saja, berubah tiap scan
    below_budget_grams = saved_today_grams(user, today)
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
            build_notifications(user, game_profile, scans_today, quests,
                                extra=rank_notifications(user, board, today)),
        ),
        "stats": {
            "scans": total_scans,
            "recordStreak": game_profile.record_streak,
            "avoidedKg": kg(below_budget_grams),
            "campusRank": rank_data["campusRank"],
            "badges": len(earned_badge_ids),
            "badgesTotal": len(badges),
        },
        "badges": badges,
    }
