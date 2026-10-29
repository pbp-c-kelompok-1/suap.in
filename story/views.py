from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Count, Max
from django.db import transaction
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.http import Http404, JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST, require_http_methods

from gamification.services import MAX_LEVEL, get_profile, tier_from_level, xp_progress

from .forms import FriendChallengeForm, StoryComicForm, StoryPageForm
from .models import FriendChallenge, StoryComic, StoryPage

from .challenge_services import (
    accept_challenge as accept_challenge_service,
    get_challenge_scores,
    refresh_challenge,
)


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
    # Admin boleh review draft. Pembaca biasa cuma dapet bab yg udh terbit
    comics = StoryComic.objects.all() if request.user.is_staff else StoryComic.objects.filter(is_published=True)
    comic = get_object_or_404(comics, bab=bab)
    profile = get_profile(request.user)
    # Cek level di server juga, soalnya URL bab bisa dibuka langsung
    if profile.level < comic.unlock_level and not request.user.is_staff:
        messages.error(request, f'Bab ini baru terbuka di Level {comic.unlock_level}.')
        return redirect('story:story_list')

    pages = comic.pages.all()
    if not pages.exists():
        raise Http404('Bab ini belum memiliki halaman terbit.')
    # pake jumlah halaman yg beneran ada di database buat navigasinya
    paginator = Paginator(pages, 1)
    # Input yang bukan angka atau kurang dari 1 = dibalikin ke awal
    # klo nomornya too big, get_page ngarahin ke halaman terakhir
    try:
        requested_page = max(1, int(request.GET.get('page', 1)))
    except (ValueError, TypeError):
        requested_page = 1
    selected = paginator.get_page(requested_page)
    # Siapkan bab selanjutnya buat ditampilkan di akhir bacaan
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

def _challenge_context(user, form=None):
    # Cuma ambil tantangan yg melibatkan akun yang lagi login
    challenges = (
        FriendChallenge.objects
        .filter(Q(challenger=user) | Q(opponent=user))
        .select_related('challenger', 'opponent', 'winner')
    )

    cards = []

    for challenge in challenges:
        error = ''

        try:
            # Sekalian cek apakah tantangan aktif udah melewati batas waktu
            # klo udah, service menyimpan hasil akhirnya.
            if challenge.status == 'active':
                challenge, scores = refresh_challenge(
                    user,
                    challenge.pk,
                )
            else:
                scores = get_challenge_scores(challenge)

            # Jangan tampilkan angka nol seolah-olah itu skor tantangan lama yang sebenarnya belum punya rincian hasil.
            if (
                challenge.status == 'finished'
                and not challenge.result_snapshot
            ):
                error = (
                    'Tantangan lama ini belum memiliki '
                    'rincian skor tersimpan.'
                )

        except ValidationError as exc:
            scores = None
            error = ' '.join(exc.messages)

        cards.append({
            'challenge': challenge,
            'scores': scores,
            'error': error,
        })

    return {
        'form': (
            form
            if form is not None
            else FriendChallengeForm(user=user)
        ),
        'cards': cards,
        'active_count': sum(
            card['challenge'].status == 'active'
            for card in cards
        ),
        'pending_count': sum(
            card['challenge'].status == 'pending'
            for card in cards
        ),
        'finished_count': sum(
            card['challenge'].status == 'finished'
            for card in cards
        ),
    }


def _challenge_response(request, message):
    # Request AJAX cukup menerima daftar terbaru.
    # klo JavaScript mati, form tetap bisa kembali lewat redirect.
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'message': message,
            'html': render_to_string(
                'story/_challenge_cards.html',
                _challenge_context(request.user),
                request=request,
            ),
        })

    messages.info(request, message)
    return redirect('story:challenge_list')


@login_required
@require_http_methods(['GET', 'POST'])
def challenge_list(request):
    form = FriendChallengeForm(
        request.POST if request.method == 'POST' else None,
        user=request.user,
    )

    if request.method == 'POST' and form.is_valid():
        challenge = form.save(commit=False)

        # Pengirim diambil dari sesi login, bukan input dari browser.
        challenge.challenger = request.user
        challenge.save()

        messages.success(
            request,
            f'Tantangan dikirim ke {challenge.opponent.username}!',
        )
        return redirect('story:challenge_list')

    return render(
        request,
        'story/challenge_list.html',
        _challenge_context(request.user, form=form),
    )


@login_required
@require_POST
def challenge_accept(request, pk):
    try:
        accept_challenge_service(request.user, pk)

    except FriendChallenge.DoesNotExist:
        raise Http404('Tantangan tidak ditemukan.')

    except ValidationError as exc:
        # Misalnya tombol diklik lagi setelah tantangan udah diterima.
        return _challenge_response(
            request,
            ' '.join(exc.messages),
        )

    return _challenge_response(
        request,
        'Tantangan diterima. Waktu main dimulai sekarang!',
    )


@login_required
@require_POST
def challenge_refresh(request, pk):
    try:
        challenge, _ = refresh_challenge(request.user, pk)

    except FriendChallenge.DoesNotExist:
        raise Http404('Tantangan tidak ditemukan.')

    except ValidationError as exc:
        return _challenge_response(
            request,
            ' '.join(exc.messages),
        )

    if challenge.status == 'finished':
        message = (
            'Waktu tantangan sudah habis. '
            'Hasil akhirnya sudah disimpan.'
        )
    else:
        message = 'Progres terbaru sudah dimuat.'

    return _challenge_response(request, message)


@login_required
@require_POST
def cancel_challenge(request, pk):
    with transaction.atomic():
        # Lock dulu supaya pembatalan nggak bertabrakan
        # dengan penerimaan tantangan oleh lawan.
        challenge = get_object_or_404(
            FriendChallenge.objects.select_for_update(),
            pk=pk,
            challenger=request.user,
            status='pending',
        )
        challenge.delete()

    return _challenge_response(
        request,
        'Tantangan dibatalkan.',
    )


# Cuma atmin yg boleh edit isi cerita
def _check_story_editor(user):
    if not user.is_staff:
        raise PermissionDenied('Hanya admin yang dapat mengelola cerita.')


def _sync_page_count(comic):
    # Hitung ulang setelah halaman berubah. klo habis, bab dibalikin jadi draft
    comic.total_pages = comic.pages.count()
    if not comic.total_pages:
        comic.is_published = False
    comic.save(update_fields=['total_pages', 'is_published'])


@login_required
def story_manage(request):
    _check_story_editor(request.user)
    return render(request, 'story/manage.html', {
        'comics': StoryComic.objects.prefetch_related('pages'),
    })


@login_required
@require_http_methods(['GET', 'POST'])
def comic_edit(request, pk=None):
    _check_story_editor(request.user)
    comic = get_object_or_404(StoryComic, pk=pk) if pk else None
    form = StoryComicForm(request.POST if request.method == 'POST' else None, instance=comic)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            saved = form.save()
            _sync_page_count(saved)
        messages.success(request, 'Bab berhasil disimpan.')
        return redirect('story:manage')
    return render(request, 'story/editor_form.html', {
        'form': form, 'heading': 'Edit bab' if comic else 'Tambah bab',
        'explanation': 'Simpan bab baru sebagai draft, tambahkan halaman, lalu terbitkan saat isinya siap.',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def comic_delete(request, pk):
    _check_story_editor(request.user)
    comic = get_object_or_404(StoryComic, pk=pk)
    if request.method == 'POST':
        comic.delete()
        messages.success(request, 'Bab beserta seluruh halamannya berhasil dihapus.')
        return redirect('story:manage')
    return render(request, 'story/editor_delete.html', {
        'item': comic, 'explanation': 'Seluruh halaman di dalam bab ini juga akan dihapus.',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def page_edit(request, comic_pk, pk=None):
    _check_story_editor(request.user)
    comic = get_object_or_404(StoryComic, pk=comic_pk)
    page = get_object_or_404(StoryPage, pk=pk, comic=comic) if pk else None
    initial = {'position': (comic.pages.aggregate(last=Max('position'))['last'] or 0) + 1}
    form = StoryPageForm(request.POST if request.method == 'POST' else None,
                         instance=page, comic=comic, initial=initial)
    if request.method == 'POST' and form.is_valid():
        with transaction.atomic():
            form.save()
            _sync_page_count(comic)
        messages.success(request, 'Halaman berhasil disimpan.')
        return redirect('story:manage')
    return render(request, 'story/editor_form.html', {
        'form': form, 'heading': 'Edit halaman' if page else 'Tambah halaman',
        'explanation': f'Bab {comic.bab}: {comic.title}. Urutan menentukan posisi bacaan dalam bab ini.',
    })


@login_required
@require_http_methods(['GET', 'POST'])
def page_delete(request, comic_pk, pk):
    _check_story_editor(request.user)
    comic = get_object_or_404(StoryComic, pk=comic_pk)
    page = get_object_or_404(StoryPage, pk=pk, comic=comic)
    if request.method == 'POST':
        with transaction.atomic():
            page.delete()
            _sync_page_count(comic)
        messages.success(request, 'Halaman berhasil dihapus.')
        return redirect('story:manage')
    return render(request, 'story/editor_delete.html', {
        'item': page, 'explanation': 'Halaman lain tetap tersimpan. Bab tanpa halaman otomatis menjadi draft.',
    })
