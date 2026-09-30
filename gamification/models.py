from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class GameProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="game_profile",
    )
    total_xp = models.PositiveIntegerField(default=0)
    level = models.PositiveSmallIntegerField(
        default=1,
        validators=[MinValueValidator(1), MaxValueValidator(50)],
    )
    current_streak = models.PositiveIntegerField(default=0)
    record_streak = models.PositiveIntegerField(default=0)
    streak_freezes = models.PositiveSmallIntegerField(default=0)
    last_activity_date = models.DateField(null=True, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=models.Q(level__gte=1, level__lte=50),
                name="gameprofile_level_1_to_50",
            ),
        ]
    
    def __str__(self):
        return f"{self.user} (Lvl {self.level})"

class Badge(models.Model):
    CRITERIA_TYPES = [
        ('scan_amount', 'Scans'),
        ('streak_duration', 'Streak'),
    ]

    code = models.SlugField(unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=100, blank=True)
    criteria_type = models.CharField(max_length=20, choices=CRITERIA_TYPES, default='scan_amount')
    threshold = models.PositiveIntegerField()

    def __str__(self):
        return self.name


class UserBadge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_badges",
    )
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE)
    earned_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "badge"], name="unique_user_badge")
        ]