"""Tantangan teman, sisi Challenge.

App story (milik tim lain) sudah menangani buat tantangan, terima, batalkan, dan
penyimpanan hasil lewat refresh_challenge. File ini TIDAK mengubah story; ia hanya
memakai fungsi story yang sudah ada, dan menambah dua hal yang dibutuhkan halaman
Challenge:

- decline_duel: penerima menolak tantangan yang masih menunggu dari notifikasi.
  Tantangan dihapus (sama seperti "Batalkan" milik pengirim di story), lalu
  pengirimnya dikabari lewat Notification milik Challenge.
- finalize_due_duels: menyimpan pemenang tantangan yang waktunya habis tanpa
  menunggu seseorang menekan "Perbarui" di halaman story.
"""
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q
from django.urls import NoReverseMatch, reverse
from django.utils import timezone

from story.models import FriendChallenge

from .models import ChallengeProfile, Notification


def story_lifecycle():
    """Modul siklus tantangan milik story (terima, hitung skor, simpan hasil).

    Modul ini baru ada setelah master digabung. Selama belum ada, fitur yang
    bergantung padanya (terima, pemenang otomatis, notifikasi hasil) dimatikan
    secara sopan, tanpa membuat Challenge error.
    """
    try:
        from story import challenge_services
    except ImportError:
        return None
    return challenge_services


def has_lifecycle():
    return story_lifecycle() is not None and hasattr(FriendChallenge, 'ends_at')


def accept_url(pk):
    """URL terima milik story, atau None bila story belum punya endpoint-nya."""
    try:
        return reverse('story:challenge_accept', args=[pk])
    except NoReverseMatch:
        return None


def duel_scores(challenge):
    """Skor kedua pihak ({'challenger': {...}, 'opponent': {...}}), atau None."""
    services = story_lifecycle()
    if services is None:
        return None
    return services.get_challenge_scores(challenge)


def _display_name(user):
    profile = ChallengeProfile.objects.filter(user=user).first()
    return (profile.display_name if profile and profile.display_name else user.username)


def decline_duel(user, pk):
    """Penerima menolak tantangan yang masih menunggu. Mengembalikan pengirimnya."""
    with transaction.atomic():
        # lock supaya klik Terima dan Tolak bersamaan tidak saling menimpa
        challenge = (
            FriendChallenge.objects.select_for_update()
            .select_related('challenger', 'opponent')
            .get(pk=pk)
        )

        if challenge.opponent_id != user.pk:
            raise PermissionDenied('Hanya penerima yang boleh menolak tantangan ini.')

        if challenge.status != 'pending':
            raise ValidationError('Tantangan ini sudah tidak menunggu jawaban.')

        challenger = challenge.challenger
        Notification.objects.get_or_create(
            user=challenger,
            key=f'challenge-declined-{challenge.pk}',
            defaults={
                'kind': 'teman', 'icon': 'sword', 'tone': 'red',
                'title': f'{_display_name(user)} menolak tantanganmu',
                'body': 'Tantangan ini tidak dilanjutkan. Coba tantang teman lain!',
                'link': reverse('story:challenge_list'),
            },
        )
        challenge.delete()
        return challenger


def finalize_due_duels(user, now=None):
    """Simpan hasil akhir tantangan aktif milik user yang waktunya sudah habis.

    Aman dipanggil berulang: tantangan yang sudah selesai dilewati, dan tantangan
    orang lain tidak disentuh. Aturan pemenang tetap milik story (refresh_challenge).
    """
    services = story_lifecycle()
    if services is None or not hasattr(FriendChallenge, 'ends_at'):
        return []

    now = now or timezone.now()
    due = (
        FriendChallenge.objects
        .filter(status='active', ends_at__lte=now)
        .filter(Q(challenger=user) | Q(opponent=user))
        .values_list('pk', flat=True)
    )
    finished = []
    for pk in due:
        try:
            challenge, _ = services.refresh_challenge(user, pk, now=now)
        except (ValidationError, FriendChallenge.DoesNotExist):
            continue
        if challenge.status == 'finished':
            finished.append(challenge)
    return finished
