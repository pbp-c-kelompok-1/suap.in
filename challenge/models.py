from django.db import models
from django.utils import timezone


class ChallengeProfile(models.Model):
    """Profil tampilan di halaman Challenge: nama tampilan, bio, dan avatar terpilih."""
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile_details')
    display_name = models.CharField(max_length=24, blank=True)
    bio = models.CharField(max_length=80, blank=True)
    avatar_id = models.PositiveSmallIntegerField(default=0)

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
