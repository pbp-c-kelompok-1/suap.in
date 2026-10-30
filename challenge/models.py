from django.db import models
from django.utils import timezone


class ChallengeProfile(models.Model):
    """Profil tampilan di halaman Challenge: nama tampilan, bio, dan avatar terpilih."""
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile_details')
    display_name = models.CharField(max_length=24, blank=True)
    bio = models.CharField(max_length=80, blank=True)
    avatar_id = models.PositiveSmallIntegerField(default=0)
    # Peringkat nasional terakhir yang sudah dilihat user (untuk notifikasi naik/turun).
    last_rank = models.PositiveIntegerField(null=True, blank=True)
    last_rank_week = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'Profil {self.user.username}'


class QuestClaim(models.Model):
    """Hadiah misi harian yang sudah diklaim user (satu misi, satu hari, satu kali)."""
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='quest_claims')
    date = models.DateField()
    quest_id = models.CharField(max_length=40)
    xp = models.PositiveSmallIntegerField(default=0)
    claimed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'date', 'quest_id'], name='unique_quest_claim_per_day'),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.quest_id} - {self.date} (+{self.xp} XP)'


class BadgeRelease(models.Model):
    """Kapan sebuah lencana mulai tersedia, dicatat di app challenge.

    Model Badge milik app gamification tidak punya tanggal rilis dan tidak kita ubah.
    Dipakai untuk notifikasi "lencana baru dirilis" (hanya untuk user yang sudah
    bergabung sebelum lencana itu muncul).
    """
    badge = models.OneToOneField('gamification.Badge', on_delete=models.CASCADE, related_name='release')
    released_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f'{self.badge_id} dirilis {self.released_at:%Y-%m-%d}'


class DailyQuestSet(models.Model):
    """Misi yang dipilih untuk satu user di satu hari.

    Disimpan supaya misinya tidak berubah-ubah sepanjang hari, dan supaya besok
    bisa dipastikan tidak sama dengan hari ini.
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='daily_quest_sets')
    date = models.DateField()
    quest_ids = models.CharField(max_length=200)   # dipisah koma, urutan tampil

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['user', 'date'], name='unique_quest_set_per_day'),
        ]

    def ids(self):
        return [q for q in self.quest_ids.split(',') if q]

    def __str__(self):
        return f'{self.user.username} {self.date}: {self.quest_ids}'


class Notification(models.Model):
    """Notifikasi yang disimpan, supaya riwayat & status baca tidak hilang.

    key  : penanda unik per user (mis. 'badge-3'), supaya kejadian yang sama
           tidak membuat notifikasi dobel.
    ephemeral : True untuk notifikasi yang hanya berlaku selagi kondisinya masih
           ada (mis. "streak terancam"). Otomatis dihapus kalau sudah tidak relevan.
    dismissed : user menghapusnya. Barisnya tetap ada supaya tidak muncul lagi.
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='challenge_notifications')
    key = models.CharField(max_length=80)
    kind = models.CharField(max_length=20)
    icon = models.CharField(max_length=30, default='bell')
    tone = models.CharField(max_length=20, default='teal')
    title = models.CharField(max_length=140)
    body = models.CharField(max_length=300, blank=True)
    link = models.CharField(max_length=60, blank=True)
    ephemeral = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    read_at = models.DateTimeField(null=True, blank=True)
    dismissed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at', '-id']
        constraints = [
            models.UniqueConstraint(fields=['user', 'key'], name='unique_notification_key_per_user'),
        ]
        indexes = [models.Index(fields=['user', 'dismissed', '-created_at'], name='chal_notif_user_idx')]

    def __str__(self):
        return f'{self.user.username}: {self.title}'


class WeeklyReport(models.Model):
    """Snapshot laporan karbon seorang user untuk satu minggu yang sudah selesai.

    Data ringkasan disimpan agar laporan historis tetap tersedia sebagai record,
    bukan hanya hasil agregasi FoodLog saat halaman dibuka. Snapshot dapat
    diperbarui secara idempoten ketika generator dijalankan kembali.
    """
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='weekly_reports')
    week_start = models.DateField()
    week_end = models.DateField()
    total_co2_grams = models.PositiveBigIntegerField(default=0)
    days_logged = models.PositiveSmallIntegerField(default=0)
    scans = models.PositiveIntegerField(default=0)
    average_daily_grams = models.FloatField(default=0)
    projection_annual_kg = models.PositiveIntegerField(null=True, blank=True)
    rank_national = models.PositiveIntegerField(null=True, blank=True)
    rank_campus = models.PositiveIntegerField(null=True, blank=True)
    # Snapshot detail per hari + metrik tampilan/delta yang dipakai template.
    data = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-week_start']
        constraints = [
            models.UniqueConstraint(fields=['user', 'week_start'], name='unique_weekly_report_per_user'),
        ]
        indexes = [models.Index(fields=['user', '-week_start'], name='chal_report_user_week_idx')]

    def __str__(self):
        return f'{self.user.username} - {self.week_start} sampai {self.week_end}'
