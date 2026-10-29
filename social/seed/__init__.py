"""Data awal (showcase) untuk peta Community dan Leaderboard.

Community: daftar post ada di community_seed.json, fotonya di social/static/social/seed/.
Leaderboard: daftar akun contoh + total XP ada di leaderboard_seed.json.
Fungsi seed_* dipakai oleh data migration (otomatis saat `migrate`, termasuk di PWS)
dan oleh perintah `python manage.py seed_community` / `seed_leaderboard`.
"""
import json
import random
from datetime import datetime, time, timedelta
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parent
SEED_JSON = SEED_DIR / 'community_seed.json'
LEADERBOARD_JSON = SEED_DIR / 'leaderboard_seed.json'
STATIC_SEED_DIR = SEED_DIR.parent / 'static' / 'social' / 'seed'
STATIC_PREFIX = 'social/seed/'


FIXTURES_DIR = SEED_DIR.parent / 'fixtures'


def ensure_canteens(University, Canteen, log=print):
    """Pastikan data kampus & kantin dari fixtures ada (untuk server yang belum loaddata)."""
    unis = {}
    for row in json.loads((FIXTURES_DIR / 'universities.json').read_text(encoding='utf-8')):
        f = row['fields']
        unis[row['pk']], _ = University.objects.get_or_create(
            short_name=f['short_name'], defaults={'name': f['name'], 'city': f.get('city', '')})
    added = 0
    for row in json.loads((FIXTURES_DIR / 'canteens.json').read_text(encoding='utf-8')):
        f = row['fields']
        _, was_created = Canteen.objects.get_or_create(
            name=f['name'], faculty=f['faculty'],
            defaults={'university': unis[f['university']], 'latitude': f['latitude'], 'longitude': f['longitude'],
                      'radius_m': f.get('radius_m', 150), 'is_active': f.get('is_active', True)})
        added += was_created
    if added:
        log(f'  {added} kantin ditambahkan dari fixtures.')


def load_entries():
    with open(SEED_JSON, encoding='utf-8') as f:
        return json.load(f)


def seed_community_posts(User, Canteen, CommunityPost, log=print, verbose=False):
    """Buat post showcase yang belum ada. Aman dijalankan berkali-kali.

    Model dikirim sebagai argumen supaya bisa dipakai dari migration (model historis).
    """
    created = skipped = 0
    users = {}
    for entry in load_entries():
        photo = entry['photo']
        if not (STATIC_SEED_DIR / photo).is_file():
            if verbose:
                log(f'  dilewati: foto {photo} belum ada di social/static/social/seed/')
            skipped += 1
            continue
        canteen = Canteen.objects.filter(name=entry['canteen']).first()
        if canteen is None:
            if verbose:
                log(f"  dilewati: kantin {entry['canteen']} tidak ditemukan")
            skipped += 1
            continue

        username = entry.get('username', 'tim.suapin')
        if username not in users:
            # akun data awal (fiktif): password '!' = tidak bisa dipakai login
            users[username], _ = User.objects.get_or_create(username=username, defaults={'password': '!'})

        # satu foto boleh dipakai di beberapa kantin, jadi kuncinya (foto, kantin)
        _, was_created = CommunityPost.objects.get_or_create(
            seed_image=STATIC_PREFIX + photo,
            canteen=canteen,
            defaults={
                'user': users[username],
                'food_name': entry.get('food_name', '')[:100],
                'price': entry.get('price'),
                'total_co2_grams': entry.get('co2_grams', 0),
                'is_shared': True,
            },
        )
        created += was_created
    log(f'  {created} post showcase dibuat, {skipped} dilewati.')
    return created


# ---------- Leaderboard ----------

# Peluang akun contoh "scan" di satu hari, sesuai gaya mainnya.
PACE_CHANCE = {'rajin': 0.85, 'biasa': 0.5, 'jarang': 0.25}
HISTORY_DAYS = 35  # cukup untuk peringkat mingguan (7 hari) dan Campus War (bulan ini)


def load_leaderboard_entries():
    with open(LEADERBOARD_JSON, encoding='utf-8') as f:
        return json.load(f)


def _level_from_xp(total_xp):
    from gamification.services import level_from_xp
    return level_from_xp(total_xp)


def recent_activity(entry, now):
    """Riwayat XP 35 hari terakhir untuk satu akun contoh: [(waktu, xp), ...], terbaru dulu.

    Acak tapi tetap (seed = username), jadi hasilnya sama tiap dijalankan di hari yang sama.
    Jumlahnya tidak pernah melebihi 90% total XP akun itu.
    """
    rng = random.Random(entry['username'])
    budget = int(entry['total_xp'] * 0.9)
    today = now.date()
    rows = []
    for days_ago in range(HISTORY_DAYS):
        if entry['pace'] == 'libur':
            chance = 0 if days_ago < 9 else 0.6  # dulu aktif, seminggu terakhir tidak main
        else:
            chance = PACE_CHANCE[entry['pace']]
        if rng.random() >= chance:
            continue
        day = datetime.combine(today - timedelta(days=days_ago), time(7, 0), tzinfo=now.tzinfo)
        for _ in range(rng.choice((1, 1, 2, 2, 3))):  # 1-3 scan sehari
            xp = 10 + rng.randint(1, 6)  # sama seperti scanner: 10 + jumlah item makanan
            if rng.random() < 0.06:
                xp += rng.choice((25, 50))  # sesekali dapat bonus tantangan
            when = day + timedelta(minutes=rng.randint(0, 14 * 60))
            if when > now:
                when = now - timedelta(minutes=rng.randint(5, 90))
            if xp > budget:
                return rows
            budget -= xp
            rows.append((when, xp))
    return rows


def _streak(dates, today):
    """Streak = jumlah hari berturut-turut ada aktivitas, dihitung mundur dari hari ini/kemarin."""
    day = today if today in dates else today - timedelta(days=1)
    count = 0
    while day in dates:
        count += 1
        day -= timedelta(days=1)
    return count


def seed_leaderboard(User, University, CampusMembership, GameProfile, XPActivity, now, log=print):
    """Buat akun contoh leaderboard + XP + kampus. Aman dijalankan berkali-kali.

    Total XP tiap akun selalu sama (dari JSON). Riwayat XP-nya dibuat ulang relatif ke `now`,
    jadi jalankan lagi sebelum demo supaya peringkat mingguan tetap ramai.
    Akun asli (yang punya password) tidak pernah disentuh.
    Sengaja pakai bulk_create/update supaya tidak memicu signal pencatat XP.
    """
    campuses = {u.short_name: u for u in University.objects.all()}
    today = now.date()
    done = 0
    for entry in load_leaderboard_entries():
        user, _ = User.objects.get_or_create(
            username=entry['username'],
            defaults={'password': '!', 'first_name': entry['first_name'], 'last_name': entry['last_name']},
        )
        if user.password != '!':
            continue  # username ini sudah dipakai akun asli

        activity = recent_activity(entry, now)
        dates = {when.date() for when, _ in activity}
        profile = {
            'total_xp': entry['total_xp'],
            'level': _level_from_xp(entry['total_xp']),
            'current_streak': _streak(dates, today),
            'last_activity_date': max(dates) if dates else None,
        }
        profile['record_streak'] = max(profile['current_streak'], 3 + entry['total_xp'] // 250)
        if not GameProfile.objects.filter(user=user).update(**profile):
            GameProfile.objects.bulk_create([GameProfile(user=user, **profile)])

        if entry.get('campus') in campuses:
            CampusMembership.objects.update_or_create(user=user, defaults={'university': campuses[entry['campus']]})

        XPActivity.objects.filter(user=user).delete()
        XPActivity.objects.bulk_create(XPActivity(user=user, amount=xp, created_at=when) for when, xp in activity)
        done += 1
    log(f'  {done} akun contoh leaderboard siap.')
    return done


def unseed_leaderboard(User, CampusMembership, GameProfile, XPActivity):
    users = User.objects.filter(username__in=[e['username'] for e in load_leaderboard_entries()], password='!')
    XPActivity.objects.filter(user__in=users).delete()
    CampusMembership.objects.filter(user__in=users).delete()
    GameProfile.objects.filter(user__in=users).delete()
