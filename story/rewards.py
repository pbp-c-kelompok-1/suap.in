from django.db import transaction
from django.utils import timezone

from gamification.models import GameProfile
from gamification.services import award_xp, get_profile

from .models import MilestoneReward


# semua syarat dan bonus (biar gampang di-adjust)
MILESTONES = (
    {
        'code': 'streak-3',
        'title': 'Mulai konsisten',
        'kind': 'streak',
        'target': 3,
        'xp': 25,
    },
    {
        'code': 'streak-7',
        'title': 'Seminggu lebih sadar',
        'kind': 'streak',
        'target': 7,
        'xp': 50,
    },
    {
        'code': 'streak-14',
        'title': 'Dua minggu bertahan',
        'kind': 'streak',
        'target': 14,
        'xp': 100,
    },
    {
        'code': 'streak-30',
        'title': 'Sebulan kebiasaan baik',
        'kind': 'streak',
        'target': 30,
        'xp': 150,
    },
    {
        'code': 'level-10',
        'title': 'Pejuang Hijau',
        'kind': 'level',
        'target': 10,
        'xp': 50,
    },
    {
        'code': 'level-20',
        'title': 'Guardian Bumi',
        'kind': 'level',
        'target': 20,
        'xp': 100,
    },
    {
        'code': 'level-35',
        'title': 'Legenda Lestari',
        'kind': 'level',
        'target': 35,
        'xp': 150,
    },
)


def sync_milestone_rewards(profile):
    # pake rekor streak, bukan streak saat ini.
    # hadiah yg udah terbuka tetap ada meskipun streak putus
    values = {
        'level': profile.level,
        'streak': profile.record_streak,
    }

    for item in MILESTONES:
        if values[item['kind']] >= item['target']:
            # klo reward nya udah ada, ambil yg lama tanpa bikin duplikat
            MilestoneReward.objects.get_or_create(
                user_id=profile.user_id,
                code=item['code'],
                defaults={
                    'title': item['title'],
                    'milestone_type': item['kind'],
                    'threshold': item['target'],
                    'xp_amount': item['xp'],
                },
            )


def reward_cards(user):
    profile = get_profile(user)

    # cek akun lama juga, just in case milestone nya udh tercapai sebelum fitur reward ini dipasang.
    sync_milestone_rewards(profile)

    owned = {
        reward.code: reward
        for reward in MilestoneReward.objects.filter(user=user)
    }
    values = {
        'level': profile.level,
        'streak': profile.record_streak,
    }
    cards = []

    for item in MILESTONES:
        reward = owned.get(item['code'])

        if reward and reward.claimed_at:
            status = 'claimed'
        elif reward:
            status = 'available'
        else:
            status = 'locked'

        # ttp kirim milestone yg terkunci supaya target berikutnya kelihatan.
        cards.append({
            **item,
            'reward': reward,
            'status': status,
            'current': min(values[item['kind']], item['target']),
            'percent': min(
                100,
                round(values[item['kind']] / item['target'] * 100),
            ),
            'label': (
                'Level'
                if item['kind'] == 'level'
                else 'Rekor streak'
            ),
        })

    return profile, cards


def claim_reward(user, pk):
    # status klaim dan tambahan XP harus sama-sama berhasil
    # klo ada yg gagal, perubahan selama transaksi ini dibatalin
    with transaction.atomic():
        # Lock profil dulu, baru reward. urutannya dibuat konsisten
        GameProfile.objects.select_for_update().get_or_create(
            user=user,
        )

        # Filter user supaya ID reward orang lain gk bisa dipakai
        reward = MilestoneReward.objects.select_for_update().get(
            pk=pk,
            user=user,
        )

        # cek di server juga jadi request berulang ga ngasih XP dua kali
        if reward.claimed_at:
            return reward, False

        reward.claimed_at = timezone.now()
        reward.save(update_fields=['claimed_at'])

        # pake service XP yang udh ada supaya perhitungan level ttp sama.
        award_xp(user, reward.xp_amount)

        return reward, True