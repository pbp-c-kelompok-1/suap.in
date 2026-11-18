"""Rate limiting sederhana untuk endpoint yang mengubah data atau mudah di-spam.

Cara kerja: setiap user (atau IP untuk tamu) punya "kuota" request per jendela waktu,
disimpan di cache Django. Kalau kuota habis, request ditolak dengan status 429
(Too Many Requests) dan pesan yang jelas, tanpa menjalankan view-nya.

Analogi: setiap user punya "kartu hitung" yang diganti baru setiap 60 detik.
Setiap klik POST -> angka di kartu +1. Kalau angkanya melewati batas -> ditolak.

Cara pakai (di views.py):
    @rate_limit('friend_request', limit=10, fallback='social:friends')
    def friend_request_send(request): ...
"""
import time
from functools import wraps

from django.contrib import messages
from django.core.cache import cache        # penyimpanan sementara yang cepat (default: memori)
from django.http import JsonResponse
from django.shortcuts import redirect

LIMIT_MESSAGE = 'Terlalu banyak permintaan. Tunggu sebentar lalu coba lagi.'


def client_id(request):
    """Siapa yang sedang dihitung kuotanya.

    Sudah login -> pakai id user (contoh 'user:5'), jadi kuota ikut akun walau pindah jaringan.
    Tamu        -> pakai alamat IP (contoh 'ip:127.0.0.1').
    """
    if request.user.is_authenticated:
        return f'user:{request.user.pk}'
    return f"ip:{request.META.get('REMOTE_ADDR', '')}"


def hit(name, request, limit, window):
    """Catat satu request. Return True kalau masih di bawah batas.

    name   : nama kuota, contoh 'friend_request' (tiap fitur punya kuota sendiri)
    limit  : jumlah request maksimal
    window : panjang jendela waktu (detik)
    """
    # Nomor jendela waktu. Contoh window=60: detik ke-0..59 -> bucket N, detik 60..119 -> bucket N+1.
    # Karena nomor bucket ikut di key, setiap menit otomatis memakai "kartu" baru.
    bucket = int(time.time() // window)
    key = f'ratelimit:{name}:{client_id(request)}:{bucket}'   # contoh 'ratelimit:friend_request:user:5:29876543'
    # add() hanya membuat key kalau BELUM ada (nilai awal 0, kedaluwarsa setelah `window` detik).
    cache.add(key, 0, window)
    try:
        count = cache.incr(key)       # tambah 1 lalu kembalikan nilai barunya
    except ValueError:  # key kedaluwarsa tepat di antara add() dan incr()
        # Kasus sangat langka: key sudah hilang sehingga incr() gagal -> mulai dari 1 lagi.
        cache.set(key, 1, window)
        count = 1
    return count <= limit


def rate_limit(name, limit, window=60, fallback=None):
    """Batasi `limit` request POST per `window` detik untuk tiap user/IP.

    fallback: nama URL tujuan redirect untuk form biasa (non-AJAX). Tanpa fallback,
    penolakan selalu dibalas JSON (cocok untuk endpoint API).

    Ini DECORATOR DENGAN PARAMETER, jadi ada 3 lapis fungsi:
        rate_limit(name, limit, ...)  -> menerima pengaturan, mengembalikan `decorator`
        decorator(view)               -> menerima fungsi view, mengembalikan `wrapped`
        wrapped(request, ...)         -> yang benar-benar dijalankan Django setiap ada request
    """
    def decorator(view):
        # @wraps(view) -> `wrapped` tetap membawa nama & docstring view asli (rapi saat debug).
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            # Hanya POST yang dihitung. Membuka halaman (GET) tidak pernah dibatasi.
            # Kalau hit() False = kuota habis -> tolak SEBELUM view dijalankan.
            if request.method == 'POST' and not hit(name, request, limit, window):
                # Form biasa (bukan fetch) dan ada fallback -> pesan merah + kembali ke halaman.
                if fallback and request.headers.get('x-requested-with') != 'fetch':
                    messages.error(request, LIMIT_MESSAGE)
                    return redirect(fallback)
                # AJAX / API -> JSON dengan status 429 Too Many Requests.
                response = JsonResponse({'ok': False, 'message': LIMIT_MESSAGE, 'error': LIMIT_MESSAGE}, status=429)
                # Header standar HTTP: beri tahu browser berapa detik harus menunggu.
                response['Retry-After'] = str(window)
                return response
            # Masih dalam kuota -> jalankan view aslinya seperti biasa.
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
