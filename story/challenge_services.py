from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from django.db.models import Count, Sum
from scanner.models import FoodLog

from .models import FriendChallenge


def accept_challenge(user, pk):
    with transaction.atomic():
        # ambil ulang dan lock datanya supaya dua request gak sama2 memulai ulang tantangan
        challenge = FriendChallenge.objects.select_for_update().get(
            pk=pk,
        )

        # pengirim dan akun lain ga boleh menerima atas nama lawan
        if challenge.opponent_id != user.pk:
            raise PermissionDenied(
                'Hanya penerima yang boleh menerima tantangan ini.'
            )

        # tantangan aktif atau selesai ga boleh diterima ulang
        if challenge.status != 'pending':
            raise ValidationError(
                'Tantangan ini sudah tidak menunggu penerimaan.'
            )

        started_at = timezone.now()

        challenge.status = 'active'
        challenge.started_at = started_at
        challenge.ends_at = started_at + timedelta(
            days=challenge.duration_days,
        )

        challenge.save(update_fields=[
            'status',
            'started_at',
            'ends_at',
        ])

        return challenge

def get_challenge_scores(challenge, now=None):
    # klo udh selesai, pake skor yang disimpan
    # log makanan yg berubah setelahnya gk ikut mengubah hasil
    if challenge.status == 'finished' and challenge.result_snapshot:
        return challenge.result_snapshot

    scores = {
        'challenger': {'count': 0, 'co2': 0.0},
        'opponent': {'count': 0, 'co2': 0.0},
    }

    # Tantangan yg belum dimulai belum punya progres
    if not challenge.started_at or not challenge.ends_at:
        return scores

    now = now or timezone.now()

    # hitung catatan kedua peserta dari waktu mulai sampai sebelum batas akhir
    # Catatan sebelum tantangan atau setelah waktunya habis ga ikut
    totals = (
        FoodLog.objects.filter(
            user_id__in=[
                challenge.challenger_id,
                challenge.opponent_id,
            ],
            scanned_at__gte=challenge.started_at,
            scanned_at__lt=challenge.ends_at,
            scanned_at__lte=now,
        )
        .order_by()
        .values('user_id')
        .annotate(
            count=Count('pk'),
            co2=Sum('co2_grams'),
        )
    )

    for row in totals:
        side = (
            'challenger'
            if row['user_id'] == challenge.challenger_id
            else 'opponent'
        )

        scores[side] = {
            'count': row['count'],
            'co2': round(row['co2'] or 0.0, 3),
        }

    return scores


def refresh_challenge(user, pk, now=None):
    now = now or timezone.now()

    with transaction.atomic():
        # Lock tantangannya supaya hasil akhir ga disimpan bersamaan oleh dua request yg berbeda
        challenge = FriendChallenge.objects.select_for_update().get(
            pk=pk,
        )

        if user.pk not in [
            challenge.challenger_id,
            challenge.opponent_id,
        ]:
            raise PermissionDenied(
                'Kamu bukan peserta tantangan ini.'
            )

        # jgn menebak waktu mulai klo datanya blm lengkap
        if challenge.status == 'active' and (
            not challenge.started_at or not challenge.ends_at
        ):
            raise ValidationError(
                'Waktu mulai dan selesai tantangan belum lengkap.'
            )

        scores = get_challenge_scores(challenge, now=now)

        # klo masih menunggu atau waktunya belum habis, cukup kembalikan status dan progres yg ada
        if challenge.status != 'active' or now < challenge.ends_at:
            return challenge, scores

        left = scores['challenger']
        right = scores['opponent']
        winner_id = None

        # Peserta tanpa catatan ga otomatis menang cuma karena total emisinya masih nol
        if left['count'] and not right['count']:
            winner_id = challenge.challenger_id

        elif right['count'] and not left['count']:
            winner_id = challenge.opponent_id

        elif left['count'] and right['count']:
            if challenge.metric == 'most_scans':
                if left['count'] > right['count']:
                    winner_id = challenge.challenger_id
                elif right['count'] > left['count']:
                    winner_id = challenge.opponent_id

            elif challenge.metric == 'lowest_co2':
                if left['co2'] < right['co2']:
                    winner_id = challenge.challenger_id
                elif right['co2'] < left['co2']:
                    winner_id = challenge.opponent_id

            else:
                raise ValidationError(
                    'Jenis tantangan tidak dikenali.'
                )

        # klo skor sama atau keduanya belum punya catatan, winner tetap kosong dan hasilnya seri.
        challenge.status = 'finished'
        challenge.winner_id = winner_id
        challenge.finished_at = now
        challenge.result_snapshot = scores

        challenge.save(update_fields=[
            'status',
            'winner',
            'finished_at',
            'result_snapshot',
        ])

        return challenge, scores