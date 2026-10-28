"""Logika pertemanan (dipakai views Teman, Leaderboard, dan modul lain lewat friends_of)."""
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone

from .models import Friendship


class FriendshipError(Exception):
    """Aksi pertemanan yang tidak diizinkan; pesannya aman ditampilkan ke user."""


def friendship_between(a, b):
    return Friendship.objects.filter(
        Q(from_user=a, to_user=b) | Q(from_user=b, to_user=a)
    ).first()


def friend_ids(user):
    accepted = Friendship.objects.filter(status=Friendship.ACCEPTED)
    sent = accepted.filter(from_user=user).values_list('to_user_id', flat=True)
    received = accepted.filter(to_user=user).values_list('from_user_id', flat=True)
    return set(sent) | set(received)


def friends_of(user):
    """Queryset User yang sudah berteman dengan user ini."""
    return User.objects.filter(pk__in=friend_ids(user)).order_by('username')


def relation_status(user, other):
    """Status dari sudut pandang `user`: none / friends / sent / received."""
    f = friendship_between(user, other)
    if f is None or f.status == Friendship.REJECTED:
        return 'none', f
    if f.status == Friendship.ACCEPTED:
        return 'friends', f
    return ('sent' if f.from_user_id == user.id else 'received'), f


def send_request(sender, receiver):
    """Create: kirim permintaan. Kalau orang itu sudah lebih dulu mengirim, langsung diterima."""
    if sender == receiver:
        raise FriendshipError('Kamu tidak bisa menambahkan dirimu sendiri.')

    existing = friendship_between(sender, receiver)
    if existing is None:
        Friendship.objects.create(from_user=sender, to_user=receiver)
        return f'Permintaan pertemanan dikirim ke {receiver.username}.'
    if existing.status == Friendship.ACCEPTED:
        raise FriendshipError(f'Kamu sudah berteman dengan {receiver.username}.')
    if existing.status == Friendship.PENDING:
        if existing.from_user_id == sender.id:
            raise FriendshipError(f'Permintaan ke {receiver.username} masih menunggu jawaban.')
        respond(existing, sender, accept=True)
        return f'{receiver.username} juga sudah mengirim permintaan. Kalian sekarang berteman!'

    # pernah ditolak: kirim ulang sebagai permintaan baru dari pengirim ini
    existing.from_user, existing.to_user = sender, receiver
    existing.status = Friendship.PENDING
    existing.responded_at = None
    existing.created_at = timezone.now()
    existing.save()
    return f'Permintaan pertemanan dikirim ke {receiver.username}.'


def respond(friendship, user, accept):
    """Update: hanya penerima yang bisa menerima/menolak permintaan yang masih menunggu."""
    if friendship.to_user_id != user.id or friendship.status != Friendship.PENDING:
        raise FriendshipError('Permintaan ini tidak bisa dijawab.')
    friendship.status = Friendship.ACCEPTED if accept else Friendship.REJECTED
    friendship.responded_at = timezone.now()
    friendship.save()
    other = friendship.from_user.username
    return f'Kamu sekarang berteman dengan {other}!' if accept else f'Permintaan dari {other} ditolak.'


def remove(friendship, user):
    """Delete: unfriend, atau batalkan permintaan yang kamu kirim."""
    if user.id not in (friendship.from_user_id, friendship.to_user_id):
        raise FriendshipError('Pertemanan tidak ditemukan.')
    if friendship.status == Friendship.PENDING and friendship.to_user_id == user.id:
        raise FriendshipError('Gunakan tombol Tolak untuk permintaan yang masuk.')
    other = friendship.other(user).username
    was_friend = friendship.status == Friendship.ACCEPTED
    friendship.delete()
    return f'Kamu tidak lagi berteman dengan {other}.' if was_friend else f'Permintaan ke {other} dibatalkan.'
