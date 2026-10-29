import sys

from django.db import migrations

from social.seed import STATIC_PREFIX, ensure_canteens, seed_community_posts


def seed(apps, schema_editor):
    if 'test' in sys.argv:
        return  # database test harus kosong; data showcase hanya untuk server/laptop
    ensure_canteens(apps.get_model('social', 'University'), apps.get_model('social', 'Canteen'))
    seed_community_posts(
        apps.get_model('auth', 'User'),
        apps.get_model('social', 'Canteen'),
        apps.get_model('social', 'CommunityPost'),
    )


def unseed(apps, schema_editor):
    CommunityPost = apps.get_model('social', 'CommunityPost')
    CommunityPost.objects.filter(seed_image__startswith=STATIC_PREFIX).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('social', '0003_communitypost_seed_image'),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
