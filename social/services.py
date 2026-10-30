from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, Sum
from django.templatetags.static import static
from django.utils import timezone
from django.utils.timesince import timesince

from scanner.models import FoodLog
from scanner.services import get_carbon_status

from .models import CampusMembership, Canteen, CommunityPost, University

# ---------- Leaderboard & Campus War (berbasis emisi CO2) ----------
# Semua peringkat memakai aturan yang SAMA dengan peringkat mingguan di Laporan
# (challenge/ranking.py, milik modul challenge):
#   - ukuran   : rata-rata gram CO2 per scan (total CO2 / jumlah scan)
#   - urutan   : makin kecil makin atas; seri -> scan lebih banyak menang, lalu username
#   - syarat   : minimal MIN_SCANS_FOR_RANK scan dalam periode itu
# Bedanya hanya periode: Peringkat (social) = sepanjang waktu, Laporan = minggu ini,
# Campus War = bulan ini.


def week_start():
    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


def month_start():
    return timezone.localdate().replace(day=1)


def start_of(day):
    """Tanggal -> datetime jam 00:00 waktu lokal (untuk filter tanggal)."""
    return timezone.make_aware(datetime.combine(day, time.min))


def min_scans():
    from challenge.ranking import MIN_SCANS_FOR_RANK
    return MIN_SCANS_FOR_RANK


# Satu foto = satu scan. Semua item dari satu foto punya ai_raw_response yang sama,
# jadi dihitung sekali; log tanpa respons AI (input manual) dihitung satu-satu.
# Rumus ini sama dengan _weekly_entries di challenge/ranking.py.
SCAN_COUNT = (
    Count('ai_raw_response', filter=~Q(ai_raw_response=''), distinct=True)
    + Count('id', filter=Q(ai_raw_response=''))
)


def carbon_entries(since=None):
    """Satu entry per user yang pernah scan: jumlah scan, total gram CO2, rata-rata per scan.

    since=None: sepanjang waktu; since=tanggal: hanya scan sejak tanggal itu.
    """
    logs = FoodLog.objects.all()
    if since is not None:
        logs = logs.filter(scanned_at__gte=start_of(since))
    rows = (
        logs.order_by()
        .values('user_id', 'user__username')
        .annotate(scans=SCAN_COUNT, co2=Sum('co2_grams'))
    )
    entries = []
    for r in rows:
        if not r['scans']:
            continue
        carbon = r['co2'] or 0
        entries.append({
            'user_id': r['user_id'],
            'username': r['user__username'],
            'scans': r['scans'],
            'carbon': carbon,
            'avg': carbon / r['scans'],
        })
    return entries


def scope_user_ids(viewer, scope):
    """Siapa saja yang ikut di tab 'friends' / 'campus' / 'national'.

    Return (set_id atau None = semua user, alasan_kosong) dengan alasan
    '' | 'login' | 'campus' | 'no_friends'.
    """
    from challenge.ranking import friend_user_ids

    if scope == 'national':
        return None, ''
    if not viewer.is_authenticated:
        return set(), 'login'
    if scope == 'campus':
        membership = CampusMembership.objects.filter(user=viewer).first()
        if membership is None:
            return set(), 'campus'
        ids = CampusMembership.objects.filter(university=membership.university_id).values_list('user_id', flat=True)
        return set(ids), ''
    ids = friend_user_ids(viewer) - {viewer.pk}  # sumber "teman" yang sama dengan Laporan
    return ids | {viewer.pk}, ('' if ids else 'no_friends')


def carbon_leaderboard(viewer, scope, since=None):
    """Peringkat CO2 untuk satu tab. Return (ranked, entry_milik_viewer_atau_None, alasan_kosong).

    `ranked` sudah diurutkan dan diberi nomor 'pos' oleh rank_entries (aturan challenge).
    """
    from challenge.ranking import rank_entries

    ids, reason = scope_user_ids(viewer, scope)
    if reason:
        return [], None, reason
    entries = carbon_entries(since)
    if ids is not None:
        entries = [e for e in entries if e['user_id'] in ids]
    mine = next((e for e in entries if viewer.is_authenticated and e['user_id'] == viewer.pk), None)
    return rank_entries(entries), mine, ''


def leaderboard_rows(ranked, viewer, limit=50):
    """Baris yang ditampilkan: `limit` teratas, plus baris viewer kalau dia di luar itu."""
    shown = ranked[:limit]
    me = next((e for e in ranked if viewer.is_authenticated and e['user_id'] == viewer.pk), None)
    if me is not None and me not in shown:
        shown = shown + [me]
    users = User.objects.select_related('campus__university').in_bulk([e['user_id'] for e in shown])
    rows = []
    for e in shown:
        rows.append({
            'pos': e['pos'],
            'user': users[e['user_id']],
            'scans': e['scans'],
            'avg': round(e['avg']),
            'kg': round(e['carbon'] / 1000, 1),
            'is_me': me is not None and e is me,
            'gap': me is not None and e is me and len(shown) > 1 and e['pos'] > shown[-2]['pos'] + 1,
        })
    return rows


def ranked_campuses(since):
    """Campus War: rata-rata gram CO2 per scan dari semua anggota kampus sejak `since`.

    Kampus dengan scan kurang dari min_scans() belum masuk peringkat dan ditaruh di bawah.
    """
    campus_of = dict(CampusMembership.objects.values_list('user_id', 'university_id'))
    totals = {}
    for e in carbon_entries(since):
        uni = campus_of.get(e['user_id'])
        if uni is None:
            continue
        t = totals.setdefault(uni, {'scans': 0, 'carbon': 0, 'active': 0})
        t['scans'] += e['scans']
        t['carbon'] += e['carbon']
        t['active'] += 1

    ranked, waiting = [], []
    for c in University.objects.annotate(member_count=Count('members')):
        t = totals.get(c.pk, {'scans': 0, 'carbon': 0, 'active': 0})
        c.scans, c.active_members = t['scans'], t['active']
        c.total_kg = round(t['carbon'] / 1000, 1)
        c.avg_exact = t['carbon'] / t['scans'] if t['scans'] else None
        c.avg_co2 = round(c.avg_exact) if t['scans'] else None
        (ranked if c.scans >= min_scans() else waiting).append(c)

    ranked.sort(key=lambda c: (c.avg_exact, -c.scans, c.short_name))
    for pos, c in enumerate(ranked, start=1):
        c.pos = pos
    waiting.sort(key=lambda c: (-c.scans, c.short_name))
    for c in waiting:
        c.pos = None
    return ranked + waiting


# ---------- Community ----------

RANGE_DAYS = {'today': 0, 'week': 6}


def community_posts_since(range_key):
    """Post publik (dibagikan & tidak disembunyikan) dalam rentang waktu tertentu."""
    posts = CommunityPost.objects.filter(is_shared=True, is_hidden=False)
    if range_key in RANGE_DAYS:
        since = timezone.localdate() - timedelta(days=RANGE_DAYS[range_key])
        posts = posts.filter(created_at__date__gte=since)
    return posts


def canteen_pins(range_key='today', faculty=''):
    """Data pin peta: tiap kantin aktif + jumlah post + rata-rata CO2 per post."""
    posts = community_posts_since(range_key)
    canteens = Canteen.objects.filter(is_active=True)
    if faculty:
        canteens = canteens.filter(faculty=faculty)

    stats = {
        row['canteen']: row
        for row in posts.filter(canteen__in=canteens)
        .values('canteen')
        .annotate(post_count=Count('id'), avg_co2=Avg('total_co2_grams'))
    }

    pins = []
    for c in canteens:
        row = stats.get(c.id, {})
        count = row.get('post_count', 0)
        avg = round(row['avg_co2']) if count else None
        pins.append({
            'id': c.id,
            'name': c.name,
            'faculty': c.faculty,
            'lat': float(c.latitude),
            'lng': float(c.longitude),
            'post_count': count,
            'avg_co2': avg,
            'status': get_carbon_status(avg)[0] if count else 'none',
        })
    return pins


POSTS_PER_PAGE = 20


def time_ago(dt):
    """'2 jam lalu' — waktu dibuat kasar sesuai PRD (tanpa jam persis)."""
    delta = timezone.now() - dt
    if delta.total_seconds() < 60:
        return 'baru saja'
    return timesince(dt).split(',')[0] + ' lalu'


def canteen_posts(canteen, range_key='today', page=1):
    """Ringkasan + satu halaman foto untuk panel kantin."""
    posts = community_posts_since(range_key).filter(canteen=canteen).select_related('user')
    summary = posts.aggregate(post_count=Count('id'), avg_co2=Avg('total_co2_grams'), avg_price=Avg('price'))

    start = (page - 1) * POSTS_PER_PAGE
    chunk = list(posts[start:start + POSTS_PER_PAGE + 1])
    has_more = len(chunk) > POSTS_PER_PAGE

    return {
        'canteen': {'id': canteen.id, 'name': canteen.name, 'faculty': canteen.faculty},
        'summary': {
            'post_count': summary['post_count'],
            'avg_co2': round(summary['avg_co2']) if summary['avg_co2'] is not None else None,
            'avg_price': round(summary['avg_price']) if summary['avg_price'] is not None else None,
        },
        'posts': [
            {
                'id': p.id,
                'photo_url': static(p.seed_image) if p.seed_image else (p.photo.url if p.photo else ''),
                'food_name': p.food_name,
                'price': p.price,
                'co2': round(p.total_co2_grams),
                'status': get_carbon_status(p.total_co2_grams)[0],
                'username': p.user.username,
                'time_ago': time_ago(p.created_at),
            }
            for p in chunk[:POSTS_PER_PAGE]
        ],
        'page': page,
        'has_more': has_more,
    }
