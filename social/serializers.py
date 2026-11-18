"""SERIALIZER modul Social (Django REST Framework) untuk aplikasi mobile Flutter.

Serializer = "penerjemah" dua arah antara objek Python dan JSON:
    - Output (Python -> JSON): serializer.data dikirim sebagai respons API.
    - Input  (JSON -> Python): serializer.is_valid() memvalidasi data yang dikirim aplikasi,
      mirip Django Forms di social/forms.py, lalu hasil bersihnya ada di serializer.validated_data.

Daftar serializer:
    UniversitySerializer        -> data kampus (untuk pilihan kampus)
    UserBriefSerializer         -> ringkasan user: id, username, kampus
    LeaderboardRowSerializer    -> satu baris leaderboard (dari services.leaderboard_rows)
    CampusRankSerializer        -> satu baris Campus War (dari services.ranked_campuses)
    FriendRowSerializer         -> satu teman + XP
    PendingRequestSerializer    -> permintaan teman masuk / keluar
    SearchResultSerializer      -> hasil pencarian user + status hubungan
    FriendRequestSerializer     -> INPUT kirim permintaan teman (username)
    FriendResponseSerializer    -> INPUT terima / tolak (action)
    CampusChoiceSerializer      -> INPUT pilih kampus (university)
"""
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import CampusMembership, Friendship, University


def campus_short_name(user):
    """Singkatan kampus user (contoh 'UI'), atau None kalau belum memilih kampus.

    user.campus adalah relasi OneToOne terbalik. Kalau barisnya tidak ada, Django melempar
    RelatedObjectDoesNotExist (turunan AttributeError), jadi getattr(..., None) aman dipakai.
    """
    membership = getattr(user, 'campus', None)
    return membership.university.short_name if membership else None


class UniversitySerializer(serializers.ModelSerializer):
    """ModelSerializer = field dibuat otomatis dari model (mirip ModelForm)."""

    class Meta:
        model = University
        fields = ['id', 'name', 'short_name', 'city']


class UserBriefSerializer(serializers.ModelSerializer):
    """Data user yang aman dibagikan ke user lain: TANPA email, password, dll."""

    # SerializerMethodField -> nilainya diambil dari method get_<nama_field>.
    campus = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'campus']

    def get_campus(self, user):
        return campus_short_name(user)


class LeaderboardRowSerializer(serializers.Serializer):
    """Satu baris leaderboard.

    Inputnya dict dari services.leaderboard_rows, contoh:
        {'pos': 1, 'user': <User>, 'scans': 5, 'avg': 420, 'kg': 2.1, 'is_me': False, 'gap': False}
    source='...' -> ambil nilai dari key/atribut lain. 'user.username' = dict['user'].username.
    """

    pos = serializers.IntegerField()
    username = serializers.CharField(source='user.username')
    campus = serializers.SerializerMethodField()
    scans = serializers.IntegerField()
    avg_co2 = serializers.IntegerField(source='avg')        # rata-rata gram CO2 per scan
    total_kg = serializers.FloatField(source='kg')          # total emisi dalam kg
    is_me = serializers.BooleanField()                      # baris milik user yang login?
    gap = serializers.BooleanField()                        # tampilkan "⋯" sebelum baris ini?

    def get_campus(self, row):
        return campus_short_name(row['user'])


class CampusRankSerializer(serializers.ModelSerializer):
    """Satu kampus di Campus War.

    Field selain id/name/short_name/city BUKAN kolom database: nilainya ditempel ke objek
    University oleh services.ranked_campuses (c.pos, c.avg_co2, ...). Karena itu ditulis manual
    dan read_only. Nilai None (kampus belum masuk peringkat) otomatis menjadi null di JSON.
    """

    pos = serializers.IntegerField(read_only=True)
    avg_co2 = serializers.IntegerField(read_only=True)
    scans = serializers.IntegerField(read_only=True)
    active_members = serializers.IntegerField(read_only=True)
    member_count = serializers.IntegerField(read_only=True)
    total_kg = serializers.FloatField(read_only=True)

    class Meta:
        model = University
        fields = ['id', 'name', 'short_name', 'city', 'pos', 'avg_co2', 'scans',
                  'active_members', 'member_count', 'total_kg']


class FriendRowSerializer(serializers.Serializer):
    """Satu teman: dict {'user': <User dengan atribut xp>, 'xp': int, 'friendship': <Friendship>}."""

    user = UserBriefSerializer()
    xp = serializers.IntegerField()
    # id Friendship dibutuhkan aplikasi untuk tombol "Hapus teman" (POST .../<id>/delete/).
    friendship_id = serializers.IntegerField(source='friendship.id')


class PendingRequestSerializer(serializers.ModelSerializer):
    """Permintaan teman yang masih menunggu (PENDING).

    `user` = "orang satunya" dilihat dari user yang login (lihat Friendship.other).
    User yang login dikirim lewat context: PendingRequestSerializer(qs, many=True, context={'me': me}).
    """

    user = serializers.SerializerMethodField()

    class Meta:
        model = Friendship
        fields = ['id', 'user', 'status', 'created_at']

    def get_user(self, friendship):
        return UserBriefSerializer(friendship.other(self.context['me'])).data


class SearchResultSerializer(serializers.Serializer):
    """Hasil pencarian: dict {'user': <User>, 'status': 'none'|'friends'|'sent'|'received', 'friendship': ...}."""

    user = UserBriefSerializer()
    status = serializers.CharField()
    friendship_id = serializers.SerializerMethodField()

    def get_friendship_id(self, row):
        # friendship bisa None (belum pernah berhubungan) -> null di JSON.
        return row['friendship'].id if row['friendship'] else None


class FriendRequestSerializer(serializers.Serializer):
    """INPUT Create Friendship: aturan sama dengan FriendRequestForm (forms.py).

    Dipakai di api_views: FriendRequestSerializer(data=request.data, context={'sender': request.user})
    """

    username = serializers.CharField(max_length=150, error_messages={
        'required': 'Username wajib diisi.',
        'blank': 'Username wajib diisi.',
    })

    def validate_username(self, value):
        """Dipanggil otomatis oleh is_valid() (aturan DRF: validate_<nama_field>).

        Menyimpan User tujuan di self.receiver supaya view tidak perlu mencarinya lagi.
        """
        username = value.strip()
        receiver = User.objects.filter(username=username).first()
        if receiver is None:
            raise serializers.ValidationError(f'User "{username}" tidak ditemukan.')
        if receiver == self.context.get('sender'):
            raise serializers.ValidationError('Kamu tidak bisa menambahkan dirimu sendiri.')
        self.receiver = receiver
        return username


class FriendResponseSerializer(serializers.Serializer):
    """INPUT Update Friendship: hanya 'accept' (terima) atau 'reject' (tolak)."""

    action = serializers.ChoiceField(choices=['accept', 'reject'], error_messages={
        'required': 'Pilih terima atau tolak.',
        'invalid_choice': 'Pilihan harus terima atau tolak.',
    })


class CampusChoiceSerializer(serializers.ModelSerializer):
    """INPUT Create/Update CampusMembership. Field user diisi view dari user yang login."""

    class Meta:
        model = CampusMembership
        fields = ['university']
        # extra_kwargs -> mengatur field yang dibuat otomatis; di sini hanya pesan error-nya.
        extra_kwargs = {'university': {'error_messages': {
            'required': 'Pilih kampus dulu.',
            'null': 'Pilih kampus dulu.',
            'does_not_exist': 'Kampus tidak ditemukan.',
            'incorrect_type': 'Kampus tidak ditemukan.',
        }}}


def first_error(serializer):
    """Pesan error pertama dari serializer, sebagai satu kalimat (pasangan forms.first_error)."""
    for errors in serializer.errors.values():
        return str(errors[0])
    return 'Data tidak valid.'
