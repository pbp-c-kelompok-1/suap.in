"""Rate limiting sederhana untuk endpoint yang mengubah data atau mudah di-spam.

Cara kerja: setiap user (atau IP untuk tamu) punya "kuota" request per jendela waktu,
disimpan di cache Django. Kalau kuota habis, request ditolak dengan status 429
(Too Many Requests) dan pesan yang jelas, tanpa menjalankan view-nya.
"""
import time
from functools import wraps

from django.contrib import messages
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import redirect

LIMIT_MESSAGE = 'Terlalu banyak permintaan. Tunggu sebentar lalu coba lagi.'


def client_id(request):
    if request.user.is_authenticated:
        return f'user:{request.user.pk}'
    return f"ip:{request.META.get('REMOTE_ADDR', '')}"


def hit(name, request, limit, window):
    """Catat satu request. Return True kalau masih di bawah batas."""
    bucket = int(time.time() // window)
    key = f'ratelimit:{name}:{client_id(request)}:{bucket}'
    cache.add(key, 0, window)
    try:
        count = cache.incr(key)
    except ValueError:  # key kedaluwarsa tepat di antara add() dan incr()
        cache.set(key, 1, window)
        count = 1
    return count <= limit


def rate_limit(name, limit, window=60, fallback=None):
    """Batasi `limit` request POST per `window` detik untuk tiap user/IP.

    fallback: nama URL tujuan redirect untuk form biasa (non-AJAX). Tanpa fallback,
    penolakan selalu dibalas JSON (cocok untuk endpoint API).
    """
    def decorator(view):
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            if request.method == 'POST' and not hit(name, request, limit, window):
                if fallback and request.headers.get('x-requested-with') != 'fetch':
                    messages.error(request, LIMIT_MESSAGE)
                    return redirect(fallback)
                response = JsonResponse({'ok': False, 'message': LIMIT_MESSAGE, 'error': LIMIT_MESSAGE}, status=429)
                response['Retry-After'] = str(window)
                return response
            return view(request, *args, **kwargs)
        return wrapped
    return decorator
