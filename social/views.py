"""VIEWS modul Social = "penerima tamu" setiap request dari browser.

Alur umum satu request:
    browser -> urls.py (cocokkan alamat) -> fungsi view di sini
            -> panggil logika (friends.py / services.py / community.py)
            -> balas: render(template HTML) ATAU JsonResponse (untuk AJAX)

View di file ini sengaja dibuat TIPIS: hanya membaca input, memanggil fungsi logika,
dan memilih bentuk balasan. Perhitungan berat ada di services.py / community.py,
aturan pertemanan ada di friends.py.

Decorator yang sering muncul (dibaca dari atas ke bawah, dijalankan sebelum view):
    @login_required -> belum login? dialihkan ke halaman login
    @require_POST   -> selain POST ditolak dengan 405 Method Not Allowed
    @rate_limit     -> terlalu sering klik? ditolak dengan 429 (lihat ratelimit.py)
"""
from django.contrib import messages                          # pesan sekali-tampil (hijau/merah) di halaman
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db.models import F, Q                            # F = merujuk kolom; Q = kondisi OR/AND
from django.db.models.functions import Coalesce              # Coalesce(a, b) = pakai a, kalau NULL pakai b
from django.views.decorators.http import require_POST
from django.http import JsonResponse                         # balasan berupa JSON (untuk fetch/AJAX)
from django.shortcuts import get_object_or_404, redirect, render

from .community import nearest_canteens
from .forms import CampusForm, FriendRequestForm, FriendResponseForm, first_error
from .friends import FriendshipError, friend_ids, relation_status, remove, respond, send_request
from .models import Canteen, CampusMembership, Friendship
from .ratelimit import rate_limit
from .services import (
    canteen_pins, canteen_posts, carbon_leaderboard, leaderboard_rows, min_scans, month_start, ranked_campuses,
)


def is_ajax(request):
    """True kalau request dikirim JavaScript kita lewat fetch().

    JavaScript di template selalu menambahkan header `X-Requested-With: fetch`.
    Request dari form HTML biasa tidak punya header ini.
    Dipakai untuk memilih: balas JSON (AJAX) atau redirect + pesan (form biasa).
    """
    return request.headers.get('x-requested-with') == 'fetch'


def is_partial(request):
    """True kalau URL berisi ?partial=1.

    Artinya JavaScript hanya butuh POTONGAN HTML (misalnya daftar peringkat saja),
    bukan halaman penuh dengan sidebar. Potongan itu lalu ditempel ke halaman tanpa reload.
    """
    return request.GET.get('partial') == '1'


# Daftar tab leaderboard: (nilai di URL, label yang tampil).
LEADERBOARD_TABS = [('friends', 'Teman'), ('campus', 'Kampus'), ('national', 'Nasional')]


def leaderboard_view(request):
    """Leaderboard sepanjang waktu, berbasis emisi CO2 dari semua scan (modul scanner).

    Aturannya sama dengan peringkat mingguan di Laporan (modul challenge): rata-rata
    gram CO2 per scan, makin kecil makin atas, minimal beberapa scan. Bedanya hanya
    periode: halaman ini menghitung semua scan, Laporan hanya minggu ini.
    ?partial=1 hanya merender daftar peringkat (dipakai saat ganti tab lewat AJAX).

    Contoh URL: /social/leaderboard/?tab=campus
    """
    # Ambil tab dari URL. Kalau tidak ada -> 'national'.
    tab = request.GET.get('tab', 'national')
    # VALIDASI: kalau isinya aneh (?tab=hack), kembalikan ke 'national'.
    # dict(LEADERBOARD_TABS) = {'friends': 'Teman', 'campus': 'Kampus', 'national': 'Nasional'}
    if tab not in dict(LEADERBOARD_TABS):
        tab = 'national'
    # ranked = list peringkat yang sudah urut & bernomor
    # mine   = data milik user yang login (atau None)
    # reason = alasan kalau list kosong: '' / 'login' / 'campus' / 'no_friends'
    ranked, mine, reason = carbon_leaderboard(request.user, tab)
    need = min_scans()  # minimal scan supaya masuk peringkat (saat ini 3)
    # Pilih template: potongan (AJAX ganti tab) atau halaman penuh.
    template = 'social/partials/leaderboard_region.html' if is_partial(request) else 'social/leaderboard.html'
    return render(request, template, {
        'tab': tab,
        'tabs': LEADERBOARD_TABS,
        'ranking': leaderboard_rows(ranked, request.user),   # baris siap tampil (top 50 + baris aku)
        'min_scans': need,
        'my_scans': mine['scans'] if mine else 0,             # jumlah scan aku
        # Berapa scan lagi supaya aku masuk peringkat. max(0, ...) supaya tidak negatif.
        'scans_needed': max(0, need - mine['scans']) if mine else need,
        # Penanda untuk template menampilkan pesan kosong yang sesuai.
        'need_login': reason == 'login',
        'need_campus': reason == 'campus',
        'no_friends': reason == 'no_friends',
    })


def campus_war_view(request):
    """Halaman Campus War: peringkat kampus berdasarkan rata-rata CO2 per scan BULAN INI."""
    membership = None
    if request.user.is_authenticated:
        # select_related('university') -> ambil data kampus sekalian dalam 1 query (JOIN).
        membership = CampusMembership.objects.filter(user=request.user).select_related('university').first()
    template = 'social/partials/campus_war_region.html' if is_partial(request) else 'social/campus_war.html'
    return render(request, template, {
        'campuses': ranked_campuses(month_start()),   # month_start() = tanggal 1 bulan ini
        'min_scans': min_scans(),
        'my_campus': membership.university if membership else None,
        # instance=membership -> dropdown otomatis terpilih kampus user saat ini (kalau sudah punya).
        'form': CampusForm(instance=membership),
    })


@login_required
@rate_limit('campus', limit=10, fallback='social:campus_war')   # maks 10 POST per menit
def choose_campus_view(request):
    """Create/Update CampusMembership. AJAX dibalas JSON, form biasa di-redirect.

    GET  -> tampilkan halaman form pilih kampus
    POST -> simpan pilihan kampus
    """
    # Kalau user sudah punya kampus, form akan MENGUBAH baris itu (Update);
    # kalau belum, form akan MEMBUAT baris baru (Create).
    instance = CampusMembership.objects.filter(user=request.user).first()
    # request.POST or None -> saat GET, POST kosong sehingga form tidak divalidasi (tidak muncul error).
    form = CampusForm(request.POST or None, instance=instance)
    if request.method == 'POST':
        if form.is_valid():
            # commit=False -> buat objeknya tapi JANGAN simpan dulu,
            # karena kolom `user` belum diisi (field user tidak ada di form).
            membership = form.save(commit=False)
            membership.user = request.user   # isi user dari yang sedang login (bukan dari input user)
            membership.save()                # baru simpan ke database
            message = f'Kampusmu sekarang {membership.university.short_name}.'
            if is_ajax(request):
                # JavaScript akan membaca JSON ini lalu memperbarui halaman tanpa reload.
                return JsonResponse({'ok': True, 'message': message, 'campus': membership.university.short_name})
            # Form biasa: simpan pesan sukses, lalu pindah ke halaman Campus War.
            messages.success(request, message)
            return redirect('social:campus_war')
        if is_ajax(request):
            # Form tidak valid + AJAX -> balas pesan error pertama dengan status 400 (Bad Request).
            return JsonResponse({'ok': False, 'message': first_error(form)}, status=400)
    # GET, atau POST tidak valid dari form biasa -> tampilkan form (beserta pesan errornya).
    return render(request, 'social/choose_campus.html', {'form': form})


# ---------- Community ----------

def community_map_view(request):
    """Halaman peta Community. Data pin TIDAK dikirim di sini, tapi diambil JS lewat api_canteens."""
    # Daftar fakultas unik untuk dropdown filter:
    # values_list('faculty', flat=True) -> ['Fasilkom', 'FT', ...]; .distinct() -> buang duplikat.
    faculties = Canteen.objects.filter(is_active=True).values_list('faculty', flat=True).distinct().order_by('faculty')
    return render(request, 'social/community_map.html', {'faculties': list(faculties)})


def api_canteens(request):
    """API JSON: data semua pin kantin untuk peta.

    Contoh: GET /social/community/api/canteens/?range=week&faculty=Fasilkom
    """
    range_key = request.GET.get('range', 'today')
    # VALIDASI: hanya 3 nilai ini yang boleh; selain itu dianggap 'today'.
    if range_key not in ('today', 'week', 'all'):
        range_key = 'today'
    faculty = request.GET.get('faculty', '')   # kosong = semua fakultas
    return JsonResponse({'range': range_key, 'canteens': canteen_pins(range_key, faculty)})


def api_canteen_posts(request, pk):
    """API JSON: ringkasan + foto-foto satu kantin (panel yang muncul saat pin diklik).

    `pk` diambil dari URL: /social/community/api/canteens/<pk>/posts/?page=2
    """
    # Kantin tidak ada / sudah nonaktif -> 404 Not Found (bukan error 500).
    canteen = get_object_or_404(Canteen, pk=pk, is_active=True)
    range_key = request.GET.get('range', 'today')
    if range_key not in ('today', 'week', 'all'):
        range_key = 'today'
    try:
        # int('abc') akan error -> ditangkap except di bawah.
        # max(1, ...) -> halaman 0 atau negatif dipaksa jadi halaman 1.
        page = max(1, int(request.GET.get('page', 1)))
    except ValueError:
        page = 1
    return JsonResponse(canteen_posts(canteen, range_key, page))


@require_POST                          # koordinat dikirim lewat POST (tidak muncul di URL/riwayat browser)
@rate_limit('nearest', limit=20)       # tanpa fallback -> selalu dibalas JSON 429
def api_nearest(request):
    """Terima lat/lng dari browser, balas 3 kantin terdekat. Koordinat tidak disimpan."""
    try:
        # request.POST['lat'] -> KeyError kalau tidak dikirim; float('abc') -> ValueError.
        lat = float(request.POST['lat'])
        lng = float(request.POST['lng'])
    except (KeyError, ValueError):
        return JsonResponse({'error': 'lat dan lng wajib berupa angka'}, status=400)
    # Latitude valid -90..90, longitude valid -180..180. Di luar itu bukan titik di bumi.
    if not (-90 <= lat <= 90 and -180 <= lng <= 180):
        return JsonResponse({'error': 'koordinat tidak valid'}, status=400)
    try:
        # accuracy = perkiraan error GPS dalam meter (dari browser). Boleh tidak dikirim.
        accuracy = float(request.POST.get('accuracy', ''))
    except ValueError:
        # float('') error -> berarti tidak dikirim / tidak valid -> anggap tidak diketahui.
        accuracy = None
    return JsonResponse(nearest_canteens(lat, lng, accuracy))


# Maksimal jumlah hasil pencarian user di halaman Teman.
SEARCH_LIMIT = 10


@login_required
def friends_view(request):
    """Read: daftar teman, permintaan masuk/keluar, dan cari user untuk ditambahkan.

    Contoh: GET /social/friends/?q=budi
    """
    me = request.user
    # Kata kunci pencarian: buang spasi, potong maksimal 50 karakter (mencegah input super panjang).
    q = request.GET.get('q', '').strip()[:50]

    # --- 1. Hasil pencarian ---
    results = []
    if q:
        # username__icontains -> "mengandung q", tidak peduli huruf besar/kecil (SQL: ILIKE '%q%').
        # .exclude(pk=me.pk) -> diri sendiri tidak ikut muncul.
        # [:SEARCH_LIMIT] -> SQL LIMIT 10.
        for u in User.objects.filter(username__icontains=q).exclude(pk=me.pk).order_by('username')[:SEARCH_LIMIT]:
            # Status hubungan menentukan tombol yang tampil (Tambah / Terima / Terkirim / Teman).
            status, friendship = relation_status(me, u)
            results.append({'user': u, 'status': status, 'friendship': friendship})

    # --- 2. Daftar teman, diurutkan berdasarkan XP terbanyak ---
    friends = (
        User.objects.filter(pk__in=friend_ids(me))
        # Ambil kampus + universitas sekalian (JOIN) -> mencegah N+1 query saat template menampilkan kampus.
        .select_related('campus__university')
        # Tambah kolom sementara `xp` dari profil game (modul gamification).
        # Coalesce(..., 0) -> user yang belum punya profil game dapat XP 0, bukan None.
        .annotate(xp=Coalesce(F('game_profile__total_xp'), 0))
        .order_by('-xp', 'username')   # XP terbesar dulu; seri -> urut username
    )
    # Dict {id_teman: baris_friendship}. Dibutuhkan untuk tombol "Hapus teman" (butuh pk friendship).
    # Ditulis sebagai dict comprehension supaya cukup 1 query, bukan 1 query per teman.
    friendships = {f.other(me).pk: f for f in Friendship.objects.filter(
        Q(from_user=me) | Q(to_user=me), status=Friendship.ACCEPTED)}
    friend_rows = [{'user': u, 'xp': u.xp, 'friendship': friendships.get(u.pk)} for u in friends]

    context = {
        'q': q,
        'results': results,
        # --- 3. Permintaan yang masuk ke aku (perlu dijawab) & yang aku kirim (menunggu) ---
        'incoming': Friendship.objects.filter(to_user=me, status=Friendship.PENDING).select_related('from_user'),
        'outgoing': Friendship.objects.filter(from_user=me, status=Friendship.PENDING).select_related('to_user'),
        'friends': friend_rows,
    }
    template = 'social/partials/friends_region.html' if is_partial(request) else 'social/friends.html'
    return render(request, template, context)


def friendship_action_response(request, func):
    """Jalankan aksi; balas JSON untuk AJAX, atau redirect + pesan untuk form biasa.

    `func` = fungsi tanpa parameter yang mengembalikan pesan sukses, atau melempar
    FriendshipError kalau gagal. Dengan pola ini, ketiga view aksi teman (kirim, jawab,
    hapus) tidak perlu menulis ulang try/except dan pemilihan JSON/redirect.
    """
    try:
        message, ok = func(), True           # berhasil -> simpan pesan suksesnya
    except FriendshipError as exc:
        message, ok = str(exc), False        # gagal -> pesan error diambil dari exception
    if is_ajax(request):
        # 200 = OK, 400 = Bad Request. JavaScript membaca `ok` & `message` untuk update tampilan.
        return JsonResponse({'ok': ok, 'message': message}, status=200 if ok else 400)
    # Form biasa (JS mati): pilih messages.success atau messages.error, lalu kembali ke halaman Teman.
    (messages.success if ok else messages.error)(request, message)
    return redirect('social:friends')


def form_action_response(request, form, action):
    """Validasi form dulu; kalau valid jalankan aksi, kalau tidak balas pesan error form.

    Error form diubah menjadi FriendshipError supaya ditangani dengan cara yang SAMA
    seperti error logika (lewat friendship_action_response).
    """
    def run():
        # Fungsi di dalam fungsi (closure): bisa memakai variabel form & action dari luar.
        if not form.is_valid():
            raise FriendshipError(first_error(form))
        return action(form)
    return friendship_action_response(request, run)


@login_required
@require_POST
@rate_limit('friend_request', limit=10, fallback='social:friends')   # maks 10 kirim permintaan per menit
def friend_request_send(request):
    """Create: kirim permintaan pertemanan ke username tertentu.

    POST /social/friends/request/   body: username=budi
    """
    form = FriendRequestForm(request.POST, sender=request.user)
    # lambda f: ... = fungsi kecil tanpa nama. f = form yang sudah valid,
    # f.receiver = objek User tujuan (diisi oleh clean_username).
    return form_action_response(request, form, lambda f: send_request(request.user, f.receiver))


@login_required
@require_POST
@rate_limit('friend_action', limit=30, fallback='social:friends')
def friend_request_respond(request, pk):
    """Update: terima atau tolak permintaan yang masuk.

    POST /social/friends/<pk>/respond/   body: action=accept atau action=reject
    """
    friendship = get_object_or_404(Friendship, pk=pk)   # pk tidak ada -> 404
    form = FriendResponseForm(request.POST)
    # f.accept = True (Terima) / False (Tolak). Cek "apakah aku penerimanya" ada di friends.respond.
    return form_action_response(request, form, lambda f: respond(friendship, request.user, f.accept))


@login_required
@require_POST
@rate_limit('friend_action', limit=30, fallback='social:friends')
def friendship_delete(request, pk):
    """Delete: unfriend atau batalkan permintaan yang dikirim.

    POST /social/friends/<pk>/delete/
    Tidak butuh form karena tidak ada input; cek kepemilikan ada di friends.remove.
    """
    friendship = get_object_or_404(Friendship, pk=pk)
    return friendship_action_response(request, lambda: remove(friendship, request.user))


def challenge_view(request, pk):
    """Placeholder halaman Tantangan 1v1 (fitur utamanya ada di modul challenge)."""
    return render(request, 'coming_soon.html', {
        'title': 'Tantangan 1v1',
        'icon': 'fire',
        'description': 'Tantang temanmu dan lihat siapa yang paling hijau.',
    })
