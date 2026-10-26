from django.db.models.signals import post_save
from django.dispatch import receiver

from gamification.models import GameProfile

from .rewards import sync_milestone_rewards


@receiver(
    post_save,
    sender=GameProfile,
    dispatch_uid='story_milestone_rewards',
)
def create_milestone_rewards(sender, instance, raw=False, **kwargs):
    # tiap profil selesai disimpan, cek milestone yg udah tercapai
    # instance di sini adalah GameProfile yang barusan disimpan

    # Lewati proses loaddata karena data pendukungnya bisa belum lengkap
    if raw:
        return

    sync_milestone_rewards(instance)
    # alurnya: profil disimpan -> signal terpanggil -> syarat dicek -> reward yg blm ada dibuat