import json
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from story.models import StoryComic, StoryPage


class Command(BaseCommand):
    help = 'Isi enam bab dan 25 halaman cerita; konten yang sudah diedit tetap dipertahankan.'

    # klo ada proses yang gagal, perubahan database selama command ini dibatalin
    @transaction.atomic
    def handle(self, *args, **options):
        # Naik ke folder story, lalu ambil file JSON yang berisi seluruh cerita.
        source = Path(__file__).resolve().parents[2] / 'data' / 'chapters.json'
        chapters = json.loads(source.read_text(encoding='utf-8'))

        # utk menghitung bab dan halaman yang baru ditambahin
        new_comics = new_pages = 0

        for entry in chapters:
            # Pisahin informasi bab dari isi halamannya karena modelnya berbeda
            metadata = {
                key: value
                for key, value in entry.items()
                if key != 'pages'
            }
            bab = metadata.pop('bab')

            # Cari berdasarkan nomor bab. klo blm ada, buat dari data JSON
            # klo udah ada, defaults nggak dipakai buat menimpa datanya.
            comic, created = StoryComic.objects.get_or_create(
                bab=bab,
                defaults=metadata,
            )
            new_comics += int(created)
            if comic.description == 'Kenapa makanan lokal lebih ringan jejaknya.':
                comic.description = metadata['description']
                comic.save(update_fields=['description'])

            for fields in entry['pages']:
                defaults = {
                    key: value
                    for key, value in fields.items()
                    if key != 'position'
                }

                # Halaman dikenalin dari bab dan urutannya
                # Jadi kalau command dijalankan lagi, halaman yang sama nggak dobel
                page, created = StoryPage.objects.get_or_create(
                    comic=comic,
                    position=fields['position'],
                    defaults=defaults,
                )

                if created:
                    # Validasi halaman yang barusan dibuat
                    # Kalau gagal, transaction.atomic membatalkan perubahan tadi
                    page.full_clean()
                    new_pages += 1

            # Hitung dari halaman yang benar2 ada di database,
            # biar jumlahnya tetap sesuai meskipun ada halaman tambahan
            comic.total_pages = comic.pages.count()
            comic.save(update_fields=['total_pages'])

        # Tampilkan jumlah data baru, bkn jumlah seluruh data yang tersimpan
        self.stdout.write(self.style.SUCCESS(
            f'Selesai: {new_comics} bab baru, {new_pages} halaman baru. '
            'Konten yang sudah ada tidak ditimpa.'
        ))