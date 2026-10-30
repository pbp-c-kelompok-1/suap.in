"""Data awal (showcase) untuk peta Community dan Leaderboard.

Community: daftar post ada di community_seed.json, fotonya di social/static/social/seed/.
Leaderboard: daftar akun contoh (nama, kampus, total XP, gaya main) ada di leaderboard_seed.json.
Riwayat scan makanannya dibuat otomatis (nilai CO2 dari scanner/fixtures/foods.json),
karena semua peringkat dihitung dari emisi CO2 per scan.
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

# Peluang akun contoh scan di satu hari, sesuai gaya mainnya.
PACE_CHANCE = {'rajin': 0.85, 'biasa': 0.5, 'jarang': 0.25}
MAX_HISTORY_DAYS = 56  # 8 minggu: cukup untuk Peringkat, Laporan mingguan + riwayatnya, dan Campus War
SEED_SCAN_PREFIX = 'seed-scan:'  # penanda scan contoh (disimpan di ai_raw_response)

# Menu contoh. Nilai CO2 per porsi sama dengan scanner/fixtures/foods.json.
CARBS = [('Nasi Putih', 240), ('Nasi Putih', 240), ('Nasi Merah', 180), ('Nasi Uduk', 480), ('Lontong', 190)]
PROTEIN = {
    'nabati': [('Tempe Goreng', 285), ('Tahu Goreng', 195), ('Telur Rebus', 198), ('Tempe Bacem', 300),
               ('Tahu Bacem', 210), ('Telur Goreng', 220)],
    'unggas_ikan': [('Ayam Goreng', 890), ('Ayam Bakar', 810), ('Ikan Goreng', 450), ('Ikan Bakar', 400),
                    ('Pecel Lele', 520), ('Geprek Ayam', 920)],
    'daging': [('Rendang Sapi', 3150), ('Sate Sapi', 2100), ('Rawon', 1800), ('Soto Betawi', 1200)],
}
VEGGIES = [('Kangkung Tumis', 120), ('Capcay', 180), ('Sayur Asem', 150)]
DRINKS = [('Es Teh Manis', 75), ('Es Jeruk', 90), ('Air Putih', 0.3), ('Kopi Susu', 340)]
ONE_DISH = [('Gado-Gado', 320), ('Ketoprak', 290), ('Soto Ayam', 650), ('Mie Ayam', 620), ('Bakso', 780),
            ('Nasi Goreng', 420)]
# Pola makan: peluang lauk nabati / unggas-ikan / daging merah.
DIETS = {
    'hijau': (0.65, 0.32, 0.03),
    'campur': (0.35, 0.53, 0.12),
    'daging': (0.12, 0.53, 0.35),
}


def load_leaderboard_entries():
    with open(LEADERBOARD_JSON, encoding='utf-8') as f:
        return json.load(f)


def _level_from_xp(total_xp):
    from gamification.services import level_from_xp
    return level_from_xp(total_xp)


def _meal(rng, diet):
    """Isi satu foto makanan: [(nama, gram CO2), ...]."""
    if rng.random() < 0.3:
        items = [rng.choice(ONE_DISH)]
    else:
        nabati, unggas, _ = DIETS[diet]
        roll = rng.random()
        group = 'nabati' if roll < nabati else 'unggas_ikan' if roll < nabati + unggas else 'daging'
        items = [rng.choice(CARBS), rng.choice(PROTEIN[group])]
        if rng.random() < 0.5:
            items.append(rng.choice(VEGGIES))
    if rng.random() < 0.4:
        items.append(rng.choice(DRINKS))
    return items


def showcase_scans(entry, now):
    """Riwayat scan satu akun contoh: [(waktu, [(nama, gram CO2), ...]), ...], terbaru dulu.

    Acak tapi tetap (seed = username), jadi hasilnya sama tiap dijalankan di hari yang sama.
    Akun dengan XP kecil dianggap pengguna baru, jadi riwayatnya lebih pendek.
    """
    rng = random.Random(entry['username'])
    diet = entry.get('diet') or rng.choice(['hijau', 'campur', 'campur', 'daging'])
    days = max(6, min(MAX_HISTORY_DAYS, entry['total_xp'] // 45))
    today = now.date()
    scans = []
    for days_ago in range(days):
        if entry['pace'] == 'libur':
            chance = 0 if days_ago < 9 else 0.6  # dulu aktif, seminggu terakhir tidak main
        else:
            chance = PACE_CHANCE[entry['pace']]
        if rng.random() >= chance:
            continue
        day = datetime.combine(today - timedelta(days=days_ago), time(7, 0), tzinfo=now.tzinfo)
        for _ in range(rng.choice((1, 1, 2, 2, 3))):  # 1-3 scan sehari
            when = day + timedelta(minutes=rng.randint(0, 14 * 60))
            if when > now:
                when = now - timedelta(minutes=rng.randint(5, 90))
            scans.append((when, _meal(rng, diet)))
    return scans


def _streak(dates, today):
    """Streak = jumlah hari berturut-turut ada scan, dihitung mundur dari hari ini/kemarin."""
    day = today if today in dates else today - timedelta(days=1)
    count = 0
    while day in dates:
        count += 1
        day -= timedelta(days=1)
    return count


def _seed_users(User):
    """{entry, user} untuk akun contoh. Akun asli (punya password) dengan nama sama dilewati."""
    pairs = []
    for entry in load_leaderboard_entries():
        user, _ = User.objects.get_or_create(
            username=entry['username'],
            defaults={'password': '!', 'first_name': entry['first_name'], 'last_name': entry['last_name']},
        )
        if user.password == '!':
            pairs.append((entry, user))
    return pairs


def seed_leaderboard_profiles(User, University, CampusMembership, GameProfile, now, log=print):
    """Akun contoh + profil game (XP, level, streak) + kampus. Aman dijalankan berkali-kali.

    Sengaja pakai bulk_create/update supaya tidak memicu logika XP modul lain.
    """
    campuses = {u.short_name: u for u in University.objects.all()}
    today = now.date()
    pairs = _seed_users(User)
    for entry, user in pairs:
        dates = {when.date() for when, _ in showcase_scans(entry, now)}
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
    log(f'  {len(pairs)} akun contoh leaderboard siap.')
    return len(pairs)


def seed_leaderboard_scans(User, FoodLog, now, log=print):
    """Buat ulang riwayat scan akun contoh relatif ke `now` (scan contoh lama dihapus dulu).

    Jalankan lagi sebelum demo supaya peringkat mingguan & Campus War tetap ramai.
    """
    pairs = _seed_users(User)
    FoodLog.objects.filter(user__in=[u for _, u in pairs], ai_raw_response__startswith=SEED_SCAN_PREFIX).delete()
    logs, times = [], []
    for entry, user in pairs:
        for n, (when, items) in enumerate(showcase_scans(entry, now)):
            key = f"{SEED_SCAN_PREFIX}{entry['username']}:{n}"
            for name, co2 in items:
                logs.append(FoodLog(user=user, custom_name=name, co2_grams=co2, ai_raw_response=key))
                times.append(when)
    created = FoodLog.objects.bulk_create(logs, batch_size=500)
    # scanned_at memakai auto_now_add, jadi waktunya diisi setelah dibuat
    for log_row, when in zip(created, times):
        log_row.scanned_at = when
    FoodLog.objects.bulk_update(created, ['scanned_at'], batch_size=500)
    log(f'  {len({log_row.ai_raw_response for log_row in created})} scan contoh dibuat.')
    return len(created)


def seed_leaderboard(User, University, CampusMembership, GameProfile, FoodLog, now, log=print):
    seed_leaderboard_profiles(User, University, CampusMembership, GameProfile, now, log=log)
    seed_leaderboard_scans(User, FoodLog, now, log=log)


def unseed_leaderboard(User, CampusMembership, GameProfile, FoodLog=None):
    users = User.objects.filter(username__in=[e['username'] for e in load_leaderboard_entries()], password='!')
    if FoodLog is not None:
        FoodLog.objects.filter(user__in=users, ai_raw_response__startswith=SEED_SCAN_PREFIX).delete()
    CampusMembership.objects.filter(user__in=users).delete()
    GameProfile.objects.filter(user__in=users).delete()
