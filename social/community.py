"""Logika Community yang dipakai dari luar app social (Scanner).

Isi file ini:
    haversine_m           -> rumus jarak 2 titik GPS (meter)
    nearest_canteens      -> 3 kantin terdekat + rekomendasi otomatis (atau alasan tidak ada)
    compress_photo        -> kecilkan foto sebelum disimpan
    parse_price           -> ubah input harga menjadi angka yang aman
    create_post_from_scan -> buat CommunityPost dari hasil scan (DIPANGGIL scanner/views.py)
"""
import base64                   # untuk decode foto yang disimpan sebagai teks base64 di session
import io                       # io.BytesIO = "file palsu" di memori (tanpa menulis ke disk)
import uuid                     # untuk nama file acak yang unik
from math import asin, cos, radians, sin, sqrt

from django.core.files.base import ContentFile   # membungkus bytes supaya bisa disimpan ke ImageField
from PIL import Image                            # Pillow, library pengolah gambar

from .models import Canteen, CommunityPost

# Konstanta (huruf besar = nilai tetap yang mudah diubah di satu tempat).
AMBIGUOUS_GAP_M = 30      # selisih jarak 2 kantin terdekat di bawah ini = jangan pilih otomatis
MAX_GPS_ACCURACY_M = 200  # GPS lebih buruk dari ini = rekomendasi tidak dipakai
MAX_PHOTO_SIDE = 1080     # sisi terpanjang foto setelah dikompres (piksel)
MAX_PRICE = 1_000_000     # harga maksimal yang masuk akal (Rp1.000.000). Underscore hanya pemisah angka.


def haversine_m(lat1, lng1, lat2, lng2):
    """Jarak antara 2 titik di permukaan bumi, dalam METER.

    Bumi dianggap bola dengan jari-jari 6.371 km. Rumus haversine dipakai karena
    lat/lng adalah sudut (derajat), bukan koordinat datar, jadi tidak bisa pakai Pythagoras biasa.
    Langkah:
        1. ubah derajat -> radian (fungsi sin/cos Python butuh radian)
        2. hitung h dengan rumus haversine
        3. jarak = 2 * R * asin(sqrt(h))
    """
    # map(radians, ...) -> jalankan radians() ke keempat angka sekaligus.
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return 2 * 6_371_000 * asin(sqrt(h))


def nearest_canteens(lat, lng, accuracy=None):
    """3 kantin terdekat + rekomendasi (atau alasan kenapa tidak ada rekomendasi).

    Koordinat hanya dipakai untuk menghitung, tidak pernah disimpan.

    Prinsip: lebih baik TIDAK menebak daripada salah memilih kantin. Rekomendasi hanya
    diberikan kalau semua cek lolos (urutannya penting, cek pertama yang gagal yang dipakai):
        1. tidak ada kantin aktif            -> reason 'no_canteen'
        2. GPS tidak akurat (> 200 m)         -> reason 'inaccurate'
        3. kantin terdekat di luar radiusnya  -> reason 'far'
        4. kantin ke-1 & ke-2 hampir sama dekat (selisih < 30 m) -> reason 'ambiguous'
    """
    # Buat pasangan (jarak, kantin) untuk setiap kantin aktif, urutkan dari jarak terkecil,
    # lalu ambil 3 pertama dengan slicing [:3].
    ranked = sorted(
        ((haversine_m(lat, lng, float(c.latitude), float(c.longitude)), c)
         for c in Canteen.objects.filter(is_active=True)),
        key=lambda pair: pair[0],    # urutkan berdasarkan elemen ke-0 = jarak
    )[:3]
    # ranked[0] = kantin terdekat -> ranked[0][0] = jaraknya, ranked[0][1] = objek kantinnya.

    recommended, reason = None, ''
    if not ranked:
        reason = 'no_canteen'
    elif accuracy is not None and accuracy > MAX_GPS_ACCURACY_M:
        reason = 'inaccurate'
    elif ranked[0][0] > ranked[0][1].radius_m:
        reason = 'far'
    elif len(ranked) > 1 and ranked[1][0] - ranked[0][0] < AMBIGUOUS_GAP_M:
        reason = 'ambiguous'
    else:
        recommended = ranked[0][1].id    # semua lolos -> rekomendasikan kantin terdekat

    return {
        'recommended': recommended,      # id kantin, atau None
        'reason': reason,                # '' kalau ada rekomendasi
        'candidates': [                  # tetap dikirim supaya user bisa memilih sendiri
            {'id': c.id, 'name': c.name, 'faculty': c.faculty, 'distance_m': round(d)}
            for d, c in ranked
        ],
    }


def compress_photo(raw_bytes):
    """Kecilkan foto: sisi terpanjang maks 1080 px, format JPEG kualitas 82.

    Tujuannya supaya penyimpanan & loading peta tidak berat (foto HP bisa > 5 MB).
    Return ContentFile (bisa langsung dimasukkan ke ImageField CommunityPost.photo).
    """
    image = Image.open(io.BytesIO(raw_bytes))
    # convert('RGB') -> buang channel transparan (PNG) karena JPEG tidak mendukung transparansi.
    image = image.convert('RGB')
    # thumbnail() mengecilkan dengan menjaga perbandingan panjang:lebar (tidak gepeng),
    # dan tidak pernah memperbesar foto yang sudah kecil.
    image.thumbnail((MAX_PHOTO_SIDE, MAX_PHOTO_SIDE))
    out = io.BytesIO()
    image.save(out, format='JPEG', quality=82, optimize=True)
    # Nama file acak, contoh 'scan_3f9a1b2c4d5e.jpg', supaya tidak bentrok antar user.
    return ContentFile(out.getvalue(), name=f'scan_{uuid.uuid4().hex[:12]}.jpg')


def parse_price(value):
    """Input harga (teks dari form) -> int yang valid, atau None.

    '15000' -> 15000 | '' / 'abc' / None -> None | '0' / '-5' / '9999999' -> None
    """
    try:
        price = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    # Hanya terima 1 sampai 1.000.000.
    return price if 0 < price <= MAX_PRICE else None


def create_post_from_scan(request, logs):
    """Dipanggil Scanner setelah FoodLog tersimpan.

    Membuat CommunityPost hanya kalau user mencentang "Bagikan ke Community".
    Tidak pernah menggagalkan penyimpanan log: kalau ada masalah, kembalikan None.

    Ini TITIK INTEGRASI dengan modul scanner (scanner/views.py memanggil fungsi ini).
    Parameter:
        request : request POST dari halaman hasil scan (berisi isian form "Bagikan")
        logs    : list FoodLog yang baru saja disimpan scanner (1 foto = beberapa makanan)
    """
    # 1. Tidak dicentang, atau tidak ada makanan -> tidak membuat post.
    if request.POST.get('community_share') != '1' or not logs:
        return None

    # 2. Foto diambil dari session (disimpan scanner saat upload), formatnya:
    #    "data:image/jpeg;base64,/9j/4AAQ..." -> bagian setelah koma = isi foto dalam base64.
    photo_data = request.session.get('scan_photo', '')
    if ',' not in photo_data:
        return None

    try:
        # split(',', 1)[1] -> ambil bagian setelah koma pertama, lalu decode base64 -> bytes -> kompres.
        photo = compress_photo(base64.b64decode(photo_data.split(',', 1)[1]))
    except Exception:
        # Foto rusak / bukan gambar -> batal membuat post, tapi scan tetap tersimpan.
        return None

    # 3. Lokasi: pilih kantin dari daftar, atau 'other' (isi lokasi sendiri).
    canteen, custom_location = None, ''
    choice = request.POST.get('community_canteen', '')
    if choice == 'other':
        custom_location = request.POST.get('community_custom_location', '').strip()[:100]
    elif choice.isdigit():
        # isdigit() memastikan isinya angka sebelum di-int(). Hanya kantin aktif yang boleh dipilih;
        # kalau id tidak ada, .first() -> None (post tetap dibuat tanpa kantin).
        canteen = Canteen.objects.filter(pk=int(choice), is_active=True).first()

    # 4. Nama makanan: pakai isian user; kalau kosong, gabungkan nama makanan hasil scan.
    food_name = request.POST.get('community_food_name', '').strip()[:100]
    if not food_name:
        food_name = ', '.join(log.custom_name for log in logs if log.custom_name)[:100]

    # 5. Simpan post. Total CO2 = jumlah CO2 semua makanan di foto ini.
    post = CommunityPost.objects.create(
        user=request.user,
        photo=photo,
        total_co2_grams=sum(log.co2_grams for log in logs),
        canteen=canteen,
        custom_location=custom_location,
        food_name=food_name,
        price=parse_price(request.POST.get('community_price')),
        is_shared=True,
    )
    # 6. Hubungkan relasi ManyToMany ke FoodLog (harus SETELAH post punya id, jadi setelah create).
    post.food_logs.set(logs)
    return post
