import uuid
from django.contrib.auth.models import User
from django.db import models


class StoryComic(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    bab = models.PositiveIntegerField(unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    unlock_level = models.PositiveIntegerField(default=1)
    total_pages = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ['bab']

    def __str__(self):
        return f"Bab {self.bab}: {self.title}"


class FriendChallenge(models.Model):
    METRIC_CHOICES = [
        ('lowest_co2', 'Emisi CO₂ terendah'),
        ('most_scans', 'Scan terbanyak'),
    ]
    DURATION_CHOICES = [
        (3, '3 hari'),
        (7, '7 hari'),
    ]
    STATUS_CHOICES = [
        ('pending', 'Menunggu'),
        ('active', 'Berlangsung'),
        ('finished', 'Selesai'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    challenger = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenges_sent')
    opponent = models.ForeignKey(User, on_delete=models.CASCADE, related_name='challenges_received')
    metric = models.CharField(max_length=20, choices=METRIC_CHOICES, default='lowest_co2')
    duration_days = models.PositiveIntegerField(choices=DURATION_CHOICES, default=7)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    winner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='challenges_won')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.challenger.username} vs {self.opponent.username}"
