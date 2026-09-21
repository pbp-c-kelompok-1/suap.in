from django.shortcuts import render


def leaderboard_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Peringkat',
        'icon': 'board',
        'description': 'Leaderboard mingguan teman, kampus, dan nasional akan hadir di sini.',
    })


def friends_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Teman',
        'icon': 'user',
        'description': 'Tambah teman dan lihat progres mereka di sini.',
    })


def campus_war_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Campus War',
        'icon': 'board',
        'description': 'Adu emisi karbon terendah antar universitas setiap bulan.',
    })


def challenge_view(request, pk):
    return render(request, 'coming_soon.html', {
        'title': 'Tantangan 1v1',
        'icon': 'fire',
        'description': 'Tantang temanmu dan lihat siapa yang paling hijau.',
    })
