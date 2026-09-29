from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import CampusForm
from .models import CampusMembership
from .services import month_start, ranked_campuses, ranked_users, week_start


def leaderboard_view(request):
    tab = request.GET.get('tab', 'national')
    users = ranked_users(week_start())
    need_login = need_campus = False

    if tab == 'campus':
        if not request.user.is_authenticated:
            need_login, users = True, users.none()
        elif not hasattr(request.user, 'campus'):
            need_campus, users = True, users.none()
        else:
            users = users.filter(campus__university=request.user.campus.university)
    elif tab == 'friends':
        users = users.none()  # menunggu friend system dari modul Nasywa

    ranking = list(users[:50])
    return render(request, 'social/leaderboard.html', {
        'tab': tab,
        'podium': ranking[:3],
        'others': ranking[3:],
        'start_rank': 4,
        'need_login': need_login,
        'need_campus': need_campus,
    })


def campus_war_view(request):
    campuses = ranked_campuses(month_start())
    my_campus = None
    if request.user.is_authenticated and hasattr(request.user, 'campus'):
        my_campus = request.user.campus.university
    return render(request, 'social/campus_war.html', {
        'campuses': campuses,
        'my_campus': my_campus,
    })


@login_required
def choose_campus_view(request):
    instance = CampusMembership.objects.filter(user=request.user).first()
    form = CampusForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        membership = form.save(commit=False)
        membership.user = request.user
        membership.save()
        return redirect('social:campus_war')
    return render(request, 'social/choose_campus.html', {'form': form})


def friends_view(request):
    return render(request, 'coming_soon.html', {
        'title': 'Teman',
        'icon': 'user',
        'description': 'Tambah teman dan lihat progres mereka di sini.',
    })


def challenge_view(request, pk):
    return render(request, 'coming_soon.html', {
        'title': 'Tantangan 1v1',
        'icon': 'fire',
        'description': 'Tantang temanmu dan lihat siapa yang paling hijau.',
    })
