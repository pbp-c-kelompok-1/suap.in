from django.contrib import admin

from .models import WeeklyReport


@admin.register(WeeklyReport)
class WeeklyReportAdmin(admin.ModelAdmin):
    list_display = ('user', 'week_start', 'week_end', 'total_co2_grams', 'scans', 'generated_at')
    list_filter = ('week_start',)
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('generated_at',)
    ordering = ('-week_start', 'user__username')
