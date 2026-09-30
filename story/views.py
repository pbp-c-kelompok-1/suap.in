from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import FriendChallengeForm
from .models import FriendChallenge, MilestoneReward, StoryComic


def story_list(request):
    # data default bab komik as placeholder (coming soon)
    if not StoryComic.objects.exists():
        initial_comics = [
            {"bab": 1, "title": "Dari Ladang ke Piring", "description": "Asal-usul nasi yang kamu makan tiap hari.", "unlock_level": 1, "total_pages": 4},
            {"bab": 2, "title": "Jejak yang Tak Terlihat", "description": "Berapa banyak karbon di balik satu porsi rendang?", "unlock_level": 5, "total_pages": 3},
            {"bab": 3, "title": "Rantai yang Terputus", "description": "Kenapa makanan lokal lebih ringan jejaknya.", "unlock_level": 15, "total_pages": 4},
            {"bab": 4, "title": "Guardian Bumi", "description": "Perjalanan berubah jadi kebiasaan.", "unlock_level": 16, "total_pages": 5},
            {"bab": 5, "title": "Suara dari Kantin", "description": "Cerita dari mahasiswa yang sudah 100 hari.", "unlock_level": 20, "total_pages": 3},
            {"bab": 6, "title": "Legenda Lestari", "description": "Babak terakhir untuk yang paling konsisten.", "unlock_level": 31, "total_pages": 6},
        ]
        for c in initial_comics:
            StoryComic.objects.create(**c)

    user_level = 12
    comics = StoryComic.objects.all()

    comic_list = []
    for comic in comics:
        comic_list.append({
            "comic": comic,
            "is_unlocked": user_level >= comic.unlock_level
        })

    context = {
        "user_level": user_level,
        "user_title": "Pejuang Hijau",
        "xp_needed": 3,
        "next_level": 13,
        "xp_percentage": 75,
        "comics": comic_list,
    }
    return render(request, "story/story_list.html", context)


def story_reader(request, bab):
    comic = get_object_or_404(StoryComic, bab=bab)
    page = int(request.GET.get('page', 1))

    context = {
        "comic": comic,
        "current_page": page,
        "has_prev": page > 1,
        "has_next": page < comic.total_pages,
        "prev_page": page - 1,
        "next_page": page + 1,
    }
    return render(request, "story/story_reader.html", context)


# ---------- Milestone Reward ----------

DEFAULT_MILESTONES = [
    {"days_required": 7, "title": "Seminggu Konsisten", "reward": "Item avatar baru"},
    {"days_required": 30, "title": "Sebulan Hijau", "reward": "Naik tier badge"},
    {"days_required": 100, "title": "100 Hari", "reward": "Masuk Hall of Fame"},
    {"days_required": 365, "title": "Setahun Penuh", "reward": "Sertifikat digital"},
]


@login_required
def milestone_list(request):
    # placeholder: streak asli nanti diambil dari modul gamification
    current_streak = 9

    for m in DEFAULT_MILESTONES:
        MilestoneReward.objects.get_or_create(
            user=request.user, days_required=m["days_required"],
            defaults={"title": m["title"], "reward": m["reward"]},
        )

    milestones = []
    for reward in MilestoneReward.objects.filter(user=request.user):
        if reward.is_claimed:
            state = "claimed"
        elif current_streak >= reward.days_required:
            state = "claimable"
        else:
            state = "locked"
        milestones.append({
            "reward": reward,
            "state": state,
            "progress": min(100, round(current_streak / reward.days_required * 100)),
        })

    context = {
        "current_streak": current_streak,
        "milestones": milestones,
    }
    return render(request, "story/milestone_list.html", context)


@login_required
@require_POST
def claim_milestone(request, pk):
    current_streak = 9  # placeholder, samakan dengan milestone_list
    reward = get_object_or_404(MilestoneReward, pk=pk, user=request.user)
    if not reward.is_claimed and current_streak >= reward.days_required:
        reward.is_claimed = True
        reward.claimed_at = timezone.now()
        reward.save()
        messages.success(request, f"Reward \"{reward.title}\" berhasil diklaim!")
    return redirect("story:milestone_list")


# ---------- Friend Challenge (1v1) ----------

@login_required
def challenge_list(request):
    form = FriendChallengeForm(request.POST or None, user=request.user)
    if request.method == "POST" and form.is_valid():
        challenge = form.save(commit=False)
        challenge.challenger = request.user
        challenge.save()
        messages.success(request, f"Tantangan dikirim ke {challenge.opponent.username}!")
        return redirect("story:challenge_list")

    challenges = (
        FriendChallenge.objects
        .filter(Q(challenger=request.user) | Q(opponent=request.user))
        .select_related("challenger", "opponent", "winner")
    )
    context = {
        "form": form,
        "challenges": challenges,
    }
    return render(request, "story/challenge_list.html", context)


@login_required
@require_POST
def cancel_challenge(request, pk):
    challenge = get_object_or_404(FriendChallenge, pk=pk, challenger=request.user, status="pending")
    challenge.delete()
    messages.success(request, "Tantangan dibatalkan.")
    return redirect("story:challenge_list")
