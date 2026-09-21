from django.http import JsonResponse
from django.shortcuts import render


def challenge_list_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Misi',
        'icon': 'mission',
        'description': 'Tiga misi harian otomatis berdasarkan kebiasaan makanmu akan muncul di sini.',
    })


def weekly_report_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Ringkasan Mingguan',
        'icon': 'log',
        'description': 'Rekap CO₂, perbandingan minggu lalu, dan proyeksi tahunan.',
    })


def api_daily_challenges(request):
    return JsonResponse({"status": "coming soon"})
