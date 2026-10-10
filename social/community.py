"""Logika Community yang dipakai dari luar app social (Scanner)."""
import base64
import io
import uuid
from math import asin, cos, radians, sin, sqrt

from django.core.files.base import ContentFile
from PIL import Image

from .models import Canteen, CommunityPost

AMBIGUOUS_GAP_M = 30      # selisih jarak 2 kantin terdekat di bawah ini = jangan pilih otomatis
MAX_GPS_ACCURACY_M = 200  # GPS lebih buruk dari ini = rekomendasi tidak dipakai
MAX_PHOTO_SIDE = 1080
MAX_PRICE = 1_000_000


def haversine_m(lat1, lng1, lat2, lng2):
    lat1, lng1, lat2, lng2 = map(radians, (lat1, lng1, lat2, lng2))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lng2 - lng1) / 2) ** 2
    return 2 * 6_371_000 * asin(sqrt(h))


def nearest_canteens(lat, lng, accuracy=None):
    """3 kantin terdekat + rekomendasi (atau alasan kenapa tidak ada rekomendasi).

    Koordinat hanya dipakai untuk menghitung, tidak pernah disimpan.
    """
    ranked = sorted(
        ((haversine_m(lat, lng, float(c.latitude), float(c.longitude)), c)
         for c in Canteen.objects.filter(is_active=True)),
        key=lambda pair: pair[0],
    )[:3]

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
        recommended = ranked[0][1].id

    return {
        'recommended': recommended,
        'reason': reason,
        'candidates': [
            {'id': c.id, 'name': c.name, 'faculty': c.faculty, 'distance_m': round(d)}
            for d, c in ranked
        ],
    }


def compress_photo(raw_bytes):
    image = Image.open(io.BytesIO(raw_bytes))
    image = image.convert('RGB')
    image.thumbnail((MAX_PHOTO_SIDE, MAX_PHOTO_SIDE))
    out = io.BytesIO()
    image.save(out, format='JPEG', quality=82, optimize=True)
    return ContentFile(out.getvalue(), name=f'scan_{uuid.uuid4().hex[:12]}.jpg')


def parse_price(value):
    try:
        price = int(str(value).strip())
    except (TypeError, ValueError):
        return None
    return price if 0 < price <= MAX_PRICE else None


def create_post_from_scan(request, logs):
    """Dipanggil Scanner setelah FoodLog tersimpan.

    Membuat CommunityPost hanya kalau user mencentang "Bagikan ke Community".
    Tidak pernah menggagalkan penyimpanan log: kalau ada masalah, kembalikan None.
    """
    if request.POST.get('community_share') != '1' or not logs:
        return None

    photo_data = request.session.get('scan_photo', '')
    if ',' not in photo_data:
        return None

    try:
        photo = compress_photo(base64.b64decode(photo_data.split(',', 1)[1]))
    except Exception:
        return None

    canteen, custom_location = None, ''
    choice = request.POST.get('community_canteen', '')
    if choice == 'other':
        custom_location = request.POST.get('community_custom_location', '').strip()[:100]
    elif choice.isdigit():
        canteen = Canteen.objects.filter(pk=int(choice), is_active=True).first()

    food_name = request.POST.get('community_food_name', '').strip()[:100]
    if not food_name:
        food_name = ', '.join(log.custom_name for log in logs if log.custom_name)[:100]

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
    post.food_logs.set(logs)
    return post
