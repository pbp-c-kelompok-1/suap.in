"""Template tag & filter buatan sendiri untuk modul Social.

Dipakai di template dengan {% load social_tags %}, lalu:
    {% community_share_form %}  -> sisipkan form "Bagikan ke Community" (di halaman hasil scan)
    {{ waktu|ago }}             -> ubah waktu jadi teks kasar "2 jam lalu"
"""
from django import template

from social.models import Canteen

# Wajib bernama `register` supaya Django mengenali tag/filter di file ini.
register = template.Library()


# inclusion_tag -> fungsi ini mengembalikan dict, lalu dict itu dipakai merender template
# 'share_to_community.html', dan hasil HTML-nya ditempel di tempat tag dipanggil.
# takes_context=True -> fungsi menerima context template (supaya bisa mengakses request).
@register.inclusion_tag('social/partials/share_to_community.html', takes_context=True)
def community_share_form(context):
    """Form "Bagikan ke Community" yang disisipkan di halaman hasil scan."""
    request = context['request']
    # Hasil deteksi AI yang disimpan modul scanner di session (atau dict kosong kalau tidak ada).
    result = request.session.get('scan_result') or {}
    # Ambil nama tiap makanan yang terdeteksi, contoh ['Nasi', 'Ayam Goreng'].
    names = [str(item.get('name', '')).strip() for item in result.get('detected_items', [])]
    return {
        # Pilihan kantin di dropdown form.
        'canteens': Canteen.objects.filter(is_active=True).order_by('faculty', 'name'),
        # Isian awal nama makanan, contoh 'Nasi, Ayam Goreng' (maks 100 karakter).
        'default_food_name': ', '.join(n for n in names if n)[:100],
    }


@register.filter
def ago(value):
    """'2 jam lalu' / 'baru saja' — waktu kasar yang sama dengan panel Community."""
    # Import di dalam fungsi: services.py baru dimuat saat filter ini benar-benar dipakai
    # (mencegah urutan import yang saling bergantung saat Django memuat templatetags).
    from social.services import time_ago
    return time_ago(value) if value else ''
