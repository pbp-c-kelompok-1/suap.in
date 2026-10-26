from datetime import timedelta

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

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