from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from gamification.services import MAX_LEVEL, get_profile, tier_from_level, xp_progress

from .forms import FriendChallengeForm
from .models import FriendChallenge, StoryComic


@login_required
def story_list(request):
    # Level dan XP ngikut akun yang lagi login.
    profile = get_profile(request.user)
    progress = xp_progress(profile)
    query = request.GET.get('q', '').strip()[:120]
    status = request.GET.get('status', 'all')
    if status not in {'all', 'unlocked', 'locked'}:
        status = 'all'

    # Ambil bab yang udah terbit dan punya halaman. Data awal diisi lewat seed_stories.
    comics = StoryComic.objects.filter(is_published=True).annotate(page_count=Count('pages')).filter(page_count__gt=0)
    # Kata kunci dicari di judul dan ringkasan, lalu disaring lagi sesuai level akun.
    if query:
        comics = comics.filter(Q(title__icontains=query) | Q(description__icontains=query))
    if status == 'unlocked':
        comics = comics.filter(unlock_level__lte=profile.level)
    elif status == 'locked':
        comics = comics.filter(unlock_level__gt=profile.level)

    context = {
        'user_level': profile.level,
        'user_title': tier_from_level(profile.level),
        'xp_current': progress['current'],
        'xp_required': progress['needed'],
        'xp_remaining': max(0, progress['needed'] - progress['current']),
        'next_level': profile.level + 1 if profile.level < MAX_LEVEL else None,
        'xp_percentage': progress['percent'],
        'query': query, 'filter_status': status,
        'comics': [{'comic': c, 'is_unlocked': profile.level >= c.unlock_level} for c in comics],
    }
    # Buat filter AJAX, cukup kirim daftar babnya. Request biasa tetap dapat halaman lengkap.
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'html': render_to_string('story/_comic_grid.html', context, request=request),
            'count': len(context['comics']),
        })
    return render(request, 'story/story_list.html', context)


@login_required
def story_reader(request, bab):
    # Admin boleh pratinjau draft. Pembaca biasa cuma dapat bab yang udah terbit.
    comics = StoryComic.objects.all() if request.user.is_staff else StoryComic.objects.filter(is_published=True)
    comic = get_object_or_404(comics, bab=bab)
    profile = get_profile(request.user)
    # Cek level di server juga, soalnya URL bab bisa dibuka langsung.
    if profile.level < comic.unlock_level and not request.user.is_staff:
        messages.error(request, f'Bab ini baru terbuka di Level {comic.unlock_level}.')
        return redirect('story:story_list')

    pages = comic.pages.all()
    if not pages.exists():
        raise Http404('Bab ini belum memiliki halaman terbit.')
    # Pakai jumlah halaman yang beneran ada di database buat navigasinya.
    paginator = Paginator(pages, 1)
    # Input yang bukan angka atau kurang dari 1 dibalikin ke awal.
    # Kalau nomornya kebesaran, get_page ngarahin ke halaman terakhir.
    try:
        requested_page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        requested_page = 1
    selected = paginator.get_page(requested_page)
    # Siapkan bab selanjutnya buat ditampilkan di akhir bacaan.
    next_comic = (StoryComic.objects.filter(is_published=True, bab__gt=comic.bab)
                  .annotate(page_count=Count('pages')).filter(page_count__gt=0).first())
    context = {
        'comic': comic, 'page': selected.object_list[0],
        'current_page': selected.number, 'page_count': paginator.num_pages,
        'has_prev': selected.has_previous(), 'has_next': selected.has_next(),
        'prev_page': selected.number - 1, 'next_page': selected.number + 1,
        'reading_percent': round(selected.number / paginator.num_pages * 100),
        'contents': pages, 'next_comic': next_comic,
        'next_comic_unlocked': bool(next_comic and (request.user.is_staff or profile.level >= next_comic.unlock_level)),
    }
    return render(request, 'story/story_reader.html', context)


# Tantangan 1v1

@login_required
def challenge_list(request):
    form = FriendChallengeForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        challenge = form.save(commit=False)
        challenge.challenger = request.user
        challenge.save()
        messages.success(request, f"Tantangan dikirim ke {challenge.opponent.username}!")
        return redirect("story:challenge_list")

    challenges = (
        FriendChallenge.objects
        .filter(Q(challenger=request.user) | Q(opponent=request.user))
        .select_related("challenger", "opponent", "winner")
    )
    context = {
        "form": form,
        "challenges": challenges,
    }
    return render(request, "story/challenge_list.html", context)


@login_required
@require_POST
def cancel_challenge(request, pk):
    challenge = get_object_or_404(FriendChallenge, pk=pk, challenger=request.user, status="pending")
    challenge.delete()
    messages.success(request, "Tantangan dibatalkan.")
    return redirect("story:challenge_list")
