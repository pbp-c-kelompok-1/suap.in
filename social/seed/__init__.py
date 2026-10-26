"""Data awal (showcase) untuk peta Community.

Daftar post ada di community_seed.json, fotonya di social/static/social/seed/.
Fungsi seed_community_posts dipakai oleh data migration (otomatis saat `migrate`,
termasuk di PWS) dan oleh perintah `python manage.py seed_community`.
"""
import json
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parent
SEED_JSON = SEED_DIR / 'community_seed.json'
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
