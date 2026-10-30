from django.db import migrations
from django.core.management import call_command


def load_initial_foods(apps, schema_editor):
    FoodItem = apps.get_model('scanner', 'FoodItem')
    if FoodItem.objects.count() >= 50:
        return
    call_command('loaddata', 'scanner/fixtures/foods.json')


def reverse_load_initial_foods(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ('scanner', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(load_initial_foods, reverse_load_initial_foods),
    ]
