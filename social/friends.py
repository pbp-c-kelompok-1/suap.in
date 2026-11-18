"""Logika pertemanan (dipakai views Teman, Leaderboard, dan modul lain lewat friends_of).

Kenapa logika ditaruh di file terpisah, bukan di views.py?
    - views.py cukup "menerima request -> memanggil fungsi di sini -> mengirim response".
    - Fungsi di sini bisa dipakai ulang modul lain (contoh: challenge/ranking.py memakai friend_ids).
    - Fungsi di sini bisa dites langsung tanpa harus membuat request HTTP.

Peta CRUD Friendship:
    Create -> send_request
    Read   -> friendship_between, friend_ids, friends_of, relation_status
    Update -> respond (terima / tolak)
    Delete -> remove (unfriend / batalkan permintaan)
"""
from django.contrib.auth.models import User
from django.db.models import Q          # Q = "kondisi" yang bisa digabung dengan | (OR) dan & (AND)
from django.utils import timezone       # timezone.now() = waktu sekarang sesuai TIME_ZONE di settings

from .models import Friendship


class FriendshipError(Exception):
    """Aksi pertemanan yang tidak diizinkan; pesannya aman ditampilkan ke user.

    Fungsi di file ini melempar (raise) error ini kalau aksinya tidak boleh,
    misalnya menambah diri sendiri. views.friendship_action_response menangkapnya
    lalu menampilkan pesannya ke user (JSON 400 atau pesan merah di halaman).
    """


def friendship_between(a, b):
    """Cari baris Friendship antara user a dan user b, dari ARAH MANA PUN.

    Baris bisa tersimpan sebagai (from=a, to=b) atau (from=b, to=a), tergantung siapa
    yang mengirim duluan. Karena itu dipakai Q(...) | Q(...) = kondisi OR:
        WHERE (from_user=a AND to_user=b) OR (from_user=b AND to_user=a)
    .first() -> ambil 1 baris pertama, atau None kalau tidak ada (tidak error).
    """
    return Friendship.objects.filter(
        Q(from_user=a, to_user=b) | Q(from_user=b, to_user=a)
    ).first()


def friend_ids(user):
    """Kembalikan set berisi id semua teman `user` (hanya yang statusnya ACCEPTED).

    Teman bisa ada di 2 posisi:
        - aku yang mengirim -> temanku ada di kolom to_user
        - aku yang menerima -> temanku ada di kolom from_user
    Keduanya diambil lalu digabung dengan operator | (union set).
    """
    # Semua hubungan yang sudah diterima.
    accepted = Friendship.objects.filter(status=Friendship.ACCEPTED)
    # values_list('to_user_id', flat=True) -> hanya ambil kolom itu sebagai list angka, contoh [3, 7].
    sent = accepted.filter(from_user=user).values_list('to_user_id', flat=True)
    received = accepted.filter(to_user=user).values_list('from_user_id', flat=True)
    # set(...) | set(...) = gabungan tanpa duplikat.
    return set(sent) | set(received)


def friends_of(user):
    """Queryset User yang sudah berteman dengan user ini.

    pk__in=... -> "WHERE id IN (3, 7, ...)". Diurutkan berdasarkan username.
    Dipakai modul lain yang butuh daftar teman dalam bentuk objek User.
    """
    return User.objects.filter(pk__in=friend_ids(user)).order_by('username')


def relation_status(user, other):
    """Status dari sudut pandang `user`: none / friends / sent / received.

    Dipakai halaman Teman untuk menentukan tombol apa yang muncul di hasil pencarian:
        'none'     -> tombol "Tambah"
        'friends'  -> label "Teman"
        'sent'     -> label "Permintaan terkirim" (aku yang mengirim, belum dijawab)
        'received' -> tombol "Terima" (dia yang mengirim ke aku)
    Return berupa tuple (status, baris_friendship_atau_None).
    """
    f = friendship_between(user, other)
    # Belum pernah ada hubungan, ATAU pernah ditolak -> dianggap 'none' supaya bisa kirim ulang.
    if f is None or f.status == Friendship.REJECTED:
        return 'none', f
    if f.status == Friendship.ACCEPTED:
        return 'friends', f
    # Sisanya pasti PENDING. Lihat siapa pengirimnya:
    # kalau from_user adalah aku -> 'sent', kalau bukan -> 'received'.
    return ('sent' if f.from_user_id == user.id else 'received'), f


def send_request(sender, receiver):
    """Create: kirim permintaan. Kalau orang itu sudah lebih dulu mengirim, langsung diterima.

    Ada 4 kemungkinan keadaan sebelum mengirim:
        (a) belum pernah ada hubungan     -> buat baris baru (PENDING)
        (b) sudah berteman                -> error
        (c) masih PENDING:
              (c1) aku yang dulu mengirim -> error (jangan kirim dobel)
              (c2) dia yang dulu mengirim -> AUTO-ACCEPT (sama-sama mau = langsung teman)
        (d) pernah ditolak (REJECTED)     -> pakai ulang baris lama sebagai permintaan baru
    Return: kalimat pesan sukses (string) untuk ditampilkan ke user.
    """
    # Jaga-jaga: form juga sudah mengecek ini, tapi fungsi ini tetap aman kalau dipanggil langsung.
    if sender == receiver:
        raise FriendshipError('Kamu tidak bisa menambahkan dirimu sendiri.')

    existing = friendship_between(sender, receiver)

    # (a) Belum ada hubungan sama sekali -> buat baris baru. status otomatis PENDING (default model).
    if existing is None:
        Friendship.objects.create(from_user=sender, to_user=receiver)
        return f'Permintaan pertemanan dikirim ke {receiver.username}.'

    # (b) Sudah berteman -> tidak ada yang perlu dikirim.
    if existing.status == Friendship.ACCEPTED:
        raise FriendshipError(f'Kamu sudah berteman dengan {receiver.username}.')

    if existing.status == Friendship.PENDING:
        # (c1) Aku sudah mengirim sebelumnya dan belum dijawab.
        if existing.from_user_id == sender.id:
            raise FriendshipError(f'Permintaan ke {receiver.username} masih menunggu jawaban.')
        # (c2) Dia sudah mengirim ke aku. Daripada membuat permintaan kedua, anggap aku
        #      menekan "Terima" -> panggil respond() dengan accept=True.
        respond(existing, sender, accept=True)
        return f'{receiver.username} juga sudah mengirim permintaan. Kalian sekarang berteman!'

    # (d) Sampai di sini berarti status REJECTED (pernah ditolak).
    # Tidak bisa membuat baris baru karena UniqueConstraint(from_user, to_user) di model,
    # jadi baris lama dipakai ulang:
    #   - arah ditukar supaya pengirim yang baru tercatat sebagai from_user
    #   - status kembali PENDING, waktu jawab dikosongkan, waktu kirim diperbarui
    existing.from_user, existing.to_user = sender, receiver
    existing.status = Friendship.PENDING
    existing.responded_at = None
    existing.created_at = timezone.now()
    existing.save()  # simpan perubahan ke database (UPDATE)
    return f'Permintaan pertemanan dikirim ke {receiver.username}.'


def respond(friendship, user, accept):
    """Update: hanya penerima yang bisa menerima/menolak permintaan yang masih menunggu.

    Parameter:
        friendship : baris Friendship yang mau dijawab
        user       : user yang sedang login (yang menekan tombol)
        accept     : True = Terima, False = Tolak
    """
    # CEK KEPEMILIKAN: yang boleh menjawab hanya to_user (penerima), dan hanya kalau masih PENDING.
    # Tanpa cek ini, user lain yang tahu id (pk) permintaan bisa menerimanya atas nama orang lain.
    if friendship.to_user_id != user.id or friendship.status != Friendship.PENDING:
        raise FriendshipError('Permintaan ini tidak bisa dijawab.')
    # Operator ternary Python: A if kondisi else B.
    friendship.status = Friendship.ACCEPTED if accept else Friendship.REJECTED
    friendship.responded_at = timezone.now()
    friendship.save()
    other = friendship.from_user.username  # nama pengirim, untuk pesan
    return f'Kamu sekarang berteman dengan {other}!' if accept else f'Permintaan dari {other} ditolak.'


def remove(friendship, user):
    """Delete: unfriend, atau batalkan permintaan yang kamu kirim.

    Aturan:
        - hanya 2 orang yang terlibat (from_user / to_user) yang boleh menghapus
        - penerima permintaan PENDING tidak boleh "menghapus", harus pakai tombol Tolak
          (supaya status REJECTED tercatat dengan benar)
    """
    # CEK KEPEMILIKAN: user harus salah satu peserta hubungan ini.
    if user.id not in (friendship.from_user_id, friendship.to_user_id):
        raise FriendshipError('Pertemanan tidak ditemukan.')
    if friendship.status == Friendship.PENDING and friendship.to_user_id == user.id:
        raise FriendshipError('Gunakan tombol Tolak untuk permintaan yang masuk.')
    # Simpan info yang dibutuhkan untuk pesan SEBELUM baris dihapus.
    other = friendship.other(user).username
    was_friend = friendship.status == Friendship.ACCEPTED
    friendship.delete()  # DELETE dari database
    # Pesan berbeda: sudah teman -> "unfriend"; masih pending -> "permintaan dibatalkan".
    return f'Kamu tidak lagi berteman dengan {other}.' if was_friend else f'Permintaan ke {other} dibatalkan.'
