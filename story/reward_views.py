from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect, render
from django.template.loader import render_to_string
from django.views.decorators.http import require_GET, require_POST

from .models import MilestoneReward
from .rewards import claim_reward, reward_cards


def _context(user):
    # ambil profil dan status tiap milestone dari fungsi yg dibuat
    profile, cards = reward_cards(user)

    return {
        'profile': profile,
        'cards': cards,
        'available_count': sum(
            card['status'] == 'available' for card in cards
        ),
        'claimed_count': sum(
            card['status'] == 'claimed' for card in cards
        ),
        'earned_count': sum(
            card['status'] != 'locked' for card in cards
        ),
    }


@login_required
@require_GET
def reward_list(request):
    return render(
        request,
        'story/reward_list.html',
        _context(request.user),
    )


@login_required
@require_POST
def reward_claim(request, pk):
    try:
        reward, claimed = claim_reward(request.user, pk)
    except MilestoneReward.DoesNotExist:
        # Reward yang ga ada atau milik akun lain akan ditolak
        raise Http404('Reward tidak ditemukan.')

    if claimed:
        message = f'Berhasil klaim {reward.xp_amount} XP!'
    else:
        message = 'Reward ini sudah pernah diklaim.'

    # klo request dari fetch, kirim hasil klaim dan tampilan terbaru
    # Ringkasan ikut diperbarui karena tambahan XP bisa bikin naik level
    if request.headers.get('Accept') == 'application/json':
        context = _context(request.user)

        return JsonResponse({
            'claimed': claimed,
            'message': message,
            'html': render_to_string(
                'story/_reward_content.html',
                context,
                request=request,
            ),
        })

    # Form tetap bisa dipakai meskipun JavaScript dimatikan
    if claimed:
        messages.success(request, message)
    else:
        messages.info(request, message)

    return redirect('story:reward_list')