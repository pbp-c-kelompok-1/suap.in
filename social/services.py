"""SERVICES modul Social = semua perhitungan untuk Leaderboard, Campus War, dan peta Community.

File ini tidak tahu apa-apa soal request/HTML. Isinya hanya: ambil data dari database,
hitung, lalu kembalikan list/dict. views.py yang memanggil fungsi-fungsi di sini.

Daftar fungsi:
    Leaderboard & Campus War
        week_start, month_start, start_of  -> bantu urusan tanggal
        min_scans                          -> syarat minimal scan (dari modul challenge)
        SCAN_COUNT                         -> rumus menghitung jumlah scan
        carbon_entries                     -> data CO2 per user
        scope_user_ids                     -> siapa yang ikut di tab Teman / Kampus / Nasional
        carbon_leaderboard                 -> peringkat 1 tab
        leaderboard_rows                   -> baris siap tampil
        ranked_campuses                    -> peringkat Campus War
    Community
        community_posts_since, canteen_pins, time_ago, canteen_posts
"""
from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.db.models import Avg, Count, Q, Sum      # fungsi agregat SQL: AVG, COUNT, SUM
from django.templatetags.static import static        # static('x.jpg') -> URL file static, contoh '/static/x.jpg'
from django.utils import timezone
from django.utils.timesince import timesince          # timesince(waktu) -> teks seperti "2 jam, 5 menit"

# Data scan diambil dari modul scanner. Modul social TIDAK menyimpan skor sendiri.
from scanner.models import FoodLog
from scanner.services import get_carbon_status        # gram CO2 -> status hijau/kuning/merah

from .models import CampusMembership, Canteen, CommunityPost, University

# ---------- Leaderboard & Campus War (berbasis emisi CO2) ----------
# Semua peringkat memakai aturan yang SAMA dengan peringkat mingguan di Laporan
# (challenge/ranking.py, milik modul challenge):
#   - ukuran   : rata-rata gram CO2 per scan (total CO2 / jumlah scan)
#   - urutan   : makin kecil makin atas; seri -> scan lebih banyak menang, lalu username
#   - syarat   : minimal MIN_SCANS_FOR_RANK scan dalam periode itu
# Bedanya hanya periode: Peringkat (social) = sepanjang waktu, Laporan = minggu ini,
# Campus War = bulan ini.
#
# Kenapa rata-rata, bukan total? Kalau total, orang yang jarang scan otomatis menang
# (totalnya kecil). Rata-rata per scan mengukur KEBIASAAN makan, jadi adil.


def week_start():
    """Tanggal hari Senin minggu ini.

    weekday(): Senin=0, Selasa=1, ..., Minggu=6.
    Contoh: hari ini Kamis (3) -> mundur 3 hari -> Senin.
    """
    today = timezone.localdate()
    return today - timedelta(days=today.weekday())


def month_start():
    """Tanggal 1 bulan ini. Dipakai Campus War (periode bulanan)."""
    return timezone.localdate().replace(day=1)


def start_of(day):
    """Tanggal -> datetime jam 00:00 waktu lokal (untuk filter tanggal).

    Kolom scanned_at bertipe datetime (ada jamnya), jadi pembandingnya juga harus datetime.
    make_aware -> menempelkan zona waktu (Asia/Jakarta) supaya tidak ada warning/geser jam.
    """
    return timezone.make_aware(datetime.combine(day, time.min))


def min_scans():
    """Minimal jumlah scan supaya masuk peringkat (saat ini 3).

    Angkanya diambil dari challenge/ranking.py supaya Leaderboard & Laporan selalu sama.
    import ditaruh DI DALAM fungsi untuk menghindari circular import
    (challenge juga meng-import dari social).
    """
    from challenge.ranking import MIN_SCANS_FOR_RANK
    return MIN_SCANS_FOR_RANK


# Satu foto = satu scan. Semua item dari satu foto punya ai_raw_response yang sama,
# jadi dihitung sekali; log tanpa respons AI (input manual) dihitung satu-satu.
# Rumus ini sama dengan _weekly_entries di challenge/ranking.py.
#
# Contoh: 1 foto berisi nasi + ayam + es teh = 3 baris FoodLog dengan ai_raw_response SAMA.
#   Bagian kiri : COUNT(DISTINCT ai_raw_response) untuk yang tidak kosong -> 1
#   Bagian kanan: COUNT(id) untuk yang ai_raw_response kosong (input manual) -> dihitung per baris
#   ~Q(...) artinya NOT (bukan kosong).
SCAN_COUNT = (
    Count('ai_raw_response', filter=~Q(ai_raw_response=''), distinct=True)
    + Count('id', filter=Q(ai_raw_response=''))
)


def carbon_entries(since=None):
    """Satu entry per user yang pernah scan: jumlah scan, total gram CO2, rata-rata per scan.

    since=None: sepanjang waktu; since=tanggal: hanya scan sejak tanggal itu.

    Contoh hasil:
        [{'user_id': 3, 'username': 'iqbal', 'scans': 5, 'carbon': 2500.0, 'avg': 500.0}, ...]
    """
    logs = FoodLog.objects.all()
    if since is not None:
        # scanned_at__gte = "lebih besar atau sama dengan" (>=) jam 00:00 tanggal `since`.
        logs = logs.filter(scanned_at__gte=start_of(since))
    rows = (
        # order_by() KOSONG -> hapus urutan bawaan model FoodLog. Kalau tidak dihapus,
        # kolom urutan ikut masuk GROUP BY dan pengelompokan per user jadi berantakan.
        logs.order_by()
        # values(...) + annotate(...) = GROUP BY user di SQL -> 1 baris per user.
        .values('user_id', 'user__username')
        .annotate(scans=SCAN_COUNT, co2=Sum('co2_grams'))
    )
    entries = []
    for r in rows:
        if not r['scans']:
            continue                     # jaga-jaga: hindari pembagian dengan nol
        carbon = r['co2'] or 0           # SUM bisa None -> anggap 0
        entries.append({
            'user_id': r['user_id'],
            'username': r['user__username'],
            'scans': r['scans'],
            'carbon': carbon,                    # total gram CO2
            'avg': carbon / r['scans'],          # rata-rata gram CO2 per scan (nilai peringkat)
        })
    return entries


def scope_user_ids(viewer, scope):
    """Siapa saja yang ikut di tab 'friends' / 'campus' / 'national'.

    Return (set_id atau None = semua user, alasan_kosong) dengan alasan
    '' | 'login' | 'campus' | 'no_friends'.

        national -> (None, '')                 semua user ikut, tanpa filter
        belum login (tab teman/kampus) -> (set(), 'login')
        campus   -> id semua anggota kampusku, atau (set(), 'campus') kalau belum pilih kampus
        friends  -> id teman + diriku, alasan 'no_friends' kalau belum punya teman
    """
    # Import di dalam fungsi untuk menghindari circular import dengan modul challenge.
    from challenge.ranking import friend_user_ids

    if scope == 'national':
        return None, ''
    if not viewer.is_authenticated:
        return set(), 'login'
    if scope == 'campus':
        membership = CampusMembership.objects.filter(user=viewer).first()
        if membership is None:
            return set(), 'campus'
        # Semua user_id yang kampusnya sama denganku.
        ids = CampusMembership.objects.filter(university=membership.university_id).values_list('user_id', flat=True)
        return set(ids), ''
    # Tab 'friends'. friend_user_ids = teman dari fitur Teman + lawan tantangan 1v1 (modul challenge),
    # jadi definisi "teman" sama dengan halaman Laporan. `- {viewer.pk}` -> buang diriku dulu.
    ids = friend_user_ids(viewer) - {viewer.pk}  # sumber "teman" yang sama dengan Laporan
    # Diriku tetap dimasukkan supaya aku bisa melihat posisiku di antara teman-teman.
    return ids | {viewer.pk}, ('' if ids else 'no_friends')


def carbon_leaderboard(viewer, scope, since=None):
    """Peringkat CO2 untuk satu tab. Return (ranked, entry_milik_viewer_atau_None, alasan_kosong).

    `ranked` sudah diurutkan dan diberi nomor 'pos' oleh rank_entries (aturan challenge).

    Langkah:
        1. tentukan siapa yang ikut (scope_user_ids)
        2. hitung CO2 semua user (carbon_entries)
        3. saring hanya user yang ikut
        4. cari data milik viewer (untuk pesan "kurang X scan lagi")
        5. urutkan + beri nomor (rank_entries)
    """
    from challenge.ranking import rank_entries

    ids, reason = scope_user_ids(viewer, scope)
    if reason:
        return [], None, reason          # ada alasan kosong -> tidak perlu menghitung apa pun
    entries = carbon_entries(since)
    if ids is not None:                  # None = tab nasional = tidak disaring
        entries = [e for e in entries if e['user_id'] in ids]
    # next(generator, None) -> ambil elemen pertama yang cocok, atau None kalau tidak ada.
    mine = next((e for e in entries if viewer.is_authenticated and e['user_id'] == viewer.pk), None)
    # rank_entries: buang yang scan < 3, urutkan (avg, -scans, username), beri 'pos' mulai 1.
    return rank_entries(entries), mine, ''


def leaderboard_rows(ranked, viewer, limit=50):
    """Baris yang ditampilkan: `limit` teratas, plus baris viewer kalau dia di luar itu.

    Contoh: aku peringkat 87 -> tampil peringkat 1..50, lalu "⋯" (gap), lalu baris aku (87).
    """
    shown = ranked[:limit]   # slicing list: 50 elemen pertama
    me = next((e for e in ranked if viewer.is_authenticated and e['user_id'] == viewer.pk), None)
    # `me not in shown` -> aku tidak termasuk 50 besar -> tempel barisku di paling bawah.
    if me is not None and me not in shown:
        shown = shown + [me]
    # in_bulk([id, ...]) -> {id: objek_user} dalam SATU query.
    # select_related('campus__university') -> kampus ikut terambil (JOIN).
    # Tanpa ini, setiap baris memicu query baru = masalah N+1 query (50 baris = 51 query).
    users = User.objects.select_related('campus__university').in_bulk([e['user_id'] for e in shown])
    rows = []
    for e in shown:
        rows.append({
            'pos': e['pos'],
            'user': users[e['user_id']],
            'scans': e['scans'],
            'avg': round(e['avg']),                    # rata-rata gram CO2 per scan, dibulatkan
            'kg': round(e['carbon'] / 1000, 1),        # total CO2 dalam kg, 1 angka di belakang koma
            # `is` = objek yang sama persis (bukan sekadar isinya sama).
            'is_me': me is not None and e is me,
            # gap = True kalau barisku "melompat" dari baris sebelumnya (contoh 50 -> 87),
            # supaya template menampilkan "⋯" di antaranya.
            'gap': me is not None and e is me and len(shown) > 1 and e['pos'] > shown[-2]['pos'] + 1,
        })
    return rows


def ranked_campuses(since):
    """Campus War: rata-rata gram CO2 per scan dari semua anggota kampus sejak `since`.

    Kampus dengan scan kurang dari min_scans() belum masuk peringkat dan ditaruh di bawah.

    Rata-rata kampus = total CO2 semua anggota / total scan semua anggota
    (bukan rata-rata dari rata-rata tiap anggota).
    """
    # {user_id: university_id} untuk semua user yang sudah memilih kampus (1 query).
    campus_of = dict(CampusMembership.objects.values_list('user_id', 'university_id'))
    # totals = {university_id: {'scans': .., 'carbon': .., 'active': ..}}
    totals = {}
    for e in carbon_entries(since):
        uni = campus_of.get(e['user_id'])
        if uni is None:
            continue                     # user ini belum pilih kampus -> tidak dihitung
        # setdefault -> kalau kampus belum ada di dict, buat dulu dengan nilai awal 0.
        t = totals.setdefault(uni, {'scans': 0, 'carbon': 0, 'active': 0})
        t['scans'] += e['scans']
        t['carbon'] += e['carbon']
        t['active'] += 1                 # jumlah anggota yang benar-benar scan di periode ini

    ranked, waiting = [], []
    # annotate(member_count=Count('members')) -> jumlah anggota tiap kampus ('members' = related_name).
    for c in University.objects.annotate(member_count=Count('members')):
        t = totals.get(c.pk, {'scans': 0, 'carbon': 0, 'active': 0})
        # Tempel atribut baru ke objek kampus supaya mudah dipakai di template.
        c.scans, c.active_members = t['scans'], t['active']
        c.total_kg = round(t['carbon'] / 1000, 1)
        # avg_exact = nilai asli untuk mengurutkan; avg_co2 = versi bulat untuk ditampilkan.
        c.avg_exact = t['carbon'] / t['scans'] if t['scans'] else None
        c.avg_co2 = round(c.avg_exact) if t['scans'] else None
        # Masuk peringkat kalau scan kampus >= 3, kalau belum masuk daftar menunggu.
        (ranked if c.scans >= min_scans() else waiting).append(c)

    # Urutkan: rata-rata terkecil dulu; seri -> scan terbanyak (minus = menurun); lalu nama kampus.
    ranked.sort(key=lambda c: (c.avg_exact, -c.scans, c.short_name))
    for pos, c in enumerate(ranked, start=1):   # enumerate start=1 -> nomor 1, 2, 3, ...
        c.pos = pos
    # Yang menunggu: urut dari scan terbanyak (paling dekat masuk peringkat), tanpa nomor.
    waiting.sort(key=lambda c: (-c.scans, c.short_name))
    for c in waiting:
        c.pos = None
    return ranked + waiting


# ---------- Community ----------

# Berapa hari ke belakang untuk tiap filter. 'today' = 0 hari (hanya hari ini),
# 'week' = 6 hari ke belakang + hari ini = 7 hari. 'all' tidak ada di sini = tanpa filter.
RANGE_DAYS = {'today': 0, 'week': 6}


def community_posts_since(range_key):
    """Post publik (dibagikan & tidak disembunyikan) dalam rentang waktu tertentu."""
    posts = CommunityPost.objects.filter(is_shared=True, is_hidden=False)
    if range_key in RANGE_DAYS:
        since = timezone.localdate() - timedelta(days=RANGE_DAYS[range_key])
        # created_at__date__gte -> ambil bagian tanggal dari created_at, lalu bandingkan >= since.
        posts = posts.filter(created_at__date__gte=since)
    return posts


def canteen_pins(range_key='today', faculty=''):
    """Data pin peta: tiap kantin aktif + jumlah post + rata-rata CO2 per post.

    Contoh satu pin:
        {'id': 1, 'name': 'Kantin Kancil', 'faculty': 'Fasilkom', 'lat': -6.36, 'lng': 106.82,
         'post_count': 4, 'avg_co2': 520, 'status': 'green'}
    """
    posts = community_posts_since(range_key)
    canteens = Canteen.objects.filter(is_active=True)
    if faculty:
        canteens = canteens.filter(faculty=faculty)

    # Hitung jumlah post & rata-rata CO2 PER KANTIN dalam 1 query (GROUP BY canteen).
    # Hasilnya diubah jadi dict {id_kantin: baris} supaya gampang dicari di loop bawah.
    stats = {
        row['canteen']: row
        for row in posts.filter(canteen__in=canteens)
        .values('canteen')
        .annotate(post_count=Count('id'), avg_co2=Avg('total_co2_grams'))
    }

    pins = []
    for c in canteens:
        row = stats.get(c.id, {})               # kantin tanpa post -> dict kosong
        count = row.get('post_count', 0)
        avg = round(row['avg_co2']) if count else None
        pins.append({
            'id': c.id,
            'name': c.name,
            'faculty': c.faculty,
            # Decimal tidak bisa langsung diubah ke JSON -> ubah ke float.
            'lat': float(c.latitude),
            'lng': float(c.longitude),
            'post_count': count,
            'avg_co2': avg,
            # get_carbon_status (modul scanner): <= 600 g hijau, <= 1200 g kuning, > 1200 g merah.
            # [0] = ambil nama statusnya saja. Kantin tanpa post -> 'none' (pin abu-abu).
            'status': get_carbon_status(avg)[0] if count else 'none',
        })
    return pins


# Jumlah foto per halaman di panel kantin.
POSTS_PER_PAGE = 20


def time_ago(dt):
    """'2 jam lalu' — waktu dibuat kasar sesuai PRD (tanpa jam persis).

    Tujuannya privasi: orang lain tidak tahu persis jam berapa kamu makan di kantin itu.
    timesince() menghasilkan "2 jam, 5 menit" -> split(',')[0] mengambil bagian pertama saja.
    """
    delta = timezone.now() - dt
    if delta.total_seconds() < 60:
        return 'baru saja'
    return timesince(dt).split(',')[0] + ' lalu'


def canteen_posts(canteen, range_key='today', page=1):
    """Ringkasan + satu halaman foto untuk panel kantin."""
    # select_related('user') -> username tiap post ikut terambil (mencegah N+1 query).
    posts = community_posts_since(range_key).filter(canteen=canteen).select_related('user')
    # aggregate -> 1 baris hasil untuk SEMUA post kantin ini (bukan per kelompok seperti annotate).
    summary = posts.aggregate(post_count=Count('id'), avg_co2=Avg('total_co2_grams'), avg_price=Avg('price'))

    # PAGINATION. Halaman 1 -> mulai index 0, halaman 2 -> index 20, dst.
    start = (page - 1) * POSTS_PER_PAGE
    # Trik "ambil 21 untuk menampilkan 20": kalau hasilnya 21, berarti masih ada halaman berikutnya.
    # Lebih hemat daripada query COUNT terpisah. Slicing queryset = SQL LIMIT/OFFSET.
    chunk = list(posts[start:start + POSTS_PER_PAGE + 1])
    has_more = len(chunk) > POSTS_PER_PAGE

    return {
        'canteen': {'id': canteen.id, 'name': canteen.name, 'faculty': canteen.faculty},
        'summary': {
            'post_count': summary['post_count'],
            # Avg bisa None kalau tidak ada post -> jangan di-round (round(None) error).
            'avg_co2': round(summary['avg_co2']) if summary['avg_co2'] is not None else None,
            'avg_price': round(summary['avg_price']) if summary['avg_price'] is not None else None,
        },
        'posts': [
            {
                'id': p.id,
                # Data seed pakai gambar static; post asli pakai file upload (media); kalau dua-duanya
                # tidak ada -> string kosong.
                'photo_url': static(p.seed_image) if p.seed_image else (p.photo.url if p.photo else ''),
                'food_name': p.food_name,
                'price': p.price,
                'co2': round(p.total_co2_grams),
                'status': get_carbon_status(p.total_co2_grams)[0],
                'username': p.user.username,
                'time_ago': time_ago(p.created_at),
            }
            # Yang dikirim hanya 20 (data ke-21 hanya dipakai untuk menentukan has_more).
            for p in chunk[:POSTS_PER_PAGE]
        ],
        'page': page,
        'has_more': has_more,
    }
