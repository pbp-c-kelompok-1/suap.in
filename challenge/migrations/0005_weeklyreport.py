# Generated for persistent weekly carbon report snapshots.
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('challenge', '0004_badge_release'),
        ('scanner', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='WeeklyReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('week_start', models.DateField()),
                ('week_end', models.DateField()),
                ('total_co2_grams', models.PositiveBigIntegerField(default=0)),
                ('days_logged', models.PositiveSmallIntegerField(default=0)),
                ('scans', models.PositiveIntegerField(default=0)),
                ('average_daily_grams', models.FloatField(default=0)),
                ('projection_annual_kg', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_national', models.PositiveIntegerField(blank=True, null=True)),
                ('rank_campus', models.PositiveIntegerField(blank=True, null=True)),
                ('data', models.JSONField(blank=True, default=dict)),
                ('generated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='weekly_reports', to='auth.user')),
            ],
            options={'ordering': ['-week_start']},
        ),
        migrations.AddConstraint(
            model_name='weeklyreport',
            constraint=models.UniqueConstraint(fields=('user', 'week_start'), name='unique_weekly_report_per_user'),
        ),
        migrations.AddIndex(
            model_name='weeklyreport',
            index=models.Index(fields=['user', '-week_start'], name='chal_report_user_week_idx'),
        ),
    ]
