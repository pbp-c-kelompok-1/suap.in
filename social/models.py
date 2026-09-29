from django.db import models
from django.contrib.auth.models import User


class University(models.Model):
    name = models.CharField(max_length=150, unique=True)
    short_name = models.CharField(max_length=20, unique=True)
    city = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.short_name

    class Meta:
        ordering = ['short_name']
        verbose_name_plural = 'Universities'


class CampusMembership(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='campus')
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='members')
    joined_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} @ {self.university.short_name}"
