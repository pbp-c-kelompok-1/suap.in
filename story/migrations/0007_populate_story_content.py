import json
from pathlib import Path

from django.db import migrations


def load_stories(apps, schema_editor):
    # Ambil model sesuai versi migration ini.
    StoryComic = apps.get_model('story', 'StoryComic')
    StoryPage = apps.get_model('story', 'StoryPage')
    database = schema_editor.connection.alias

    # Baca naskah yang udah disalin ke folder migrations.
    source = Path(__file__).with_name('initial_story_content.json')
    chapters = json.loads(source.read_text(encoding='utf-8'))

    for chapter in chapters:
        # Pisahin informasi bab dari isi halamannya.
        metadata = {
            key: value
            for key, value in chapter.items()
            if key not in ['bab', 'pages']
        }
        metadata['is_published'] = True

        # Kalau babnya udah ada, jangan timpa editan yang lama.
        comic, _ = StoryComic.objects.using(database).get_or_create(
            bab=chapter['bab'],
            defaults=metadata,
        )

        for page in chapter['pages']:
            content = {
                key: value
                for key, value in page.items()
                if key != 'position'
            }

            # Nomor halaman dicek dalam bab yang sama biar nggak dobel.
            StoryPage.objects.using(database).get_or_create(
                comic_id=comic.pk,
                position=page['position'],
                defaults=content,
            )

        # Samain jumlah halaman dengan yang tersimpan di database.
        comic.total_pages = (
            StoryPage.objects.using(database)
            .filter(comic_id=comic.pk)
            .count()
        )
        comic.save(
            using=database,
            update_fields=['total_pages'],
        )


class Migration(migrations.Migration):
    dependencies = [
        ('story', '0006_friendchallenge_result_snapshot'),
    ]

    operations = [
        # Kalau di-rollback, cerita yang udah masuk tetap disimpan.
        migrations.RunPython(
            load_stories,
            migrations.RunPython.noop,
        ),
    ]