"""Catat setiap kenaikan XP dari modul gamification ke XPActivity.

Tidak mengubah kode gamification: cukup mendengarkan saat GameProfile disimpan.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from gamification.models import GameProfile

from .models import XPActivity


@receiver(pre_save, sender=GameProfile)
def remember_old_xp(sender, instance, **kwargs):
    old = None
    if instance.pk:
        old = sender.objects.filter(pk=instance.pk).values_list('total_xp', flat=True).first()
    instance._old_total_xp = old or 0


@receiver(post_save, sender=GameProfile)
def log_xp_gain(sender, instance, raw=False, **kwargs):
    if raw:  # loaddata fixture: bukan XP yang benar-benar didapat
        return
    gained = instance.total_xp - getattr(instance, '_old_total_xp', 0)
    if gained > 0:
        XPActivity.objects.create(user_id=instance.user_id, amount=gained)
