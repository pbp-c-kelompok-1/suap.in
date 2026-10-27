from django.db import models


class ChallengeProfile(models.Model):
    """Profil tampilan di halaman Challenge: nama tampilan, bio, dan avatar terpilih."""
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile_details')
    display_name = models.CharField(max_length=24, blank=True)
    bio = models.CharField(max_length=80, blank=True)
    avatar_id = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return f'Profil {self.user.username}'