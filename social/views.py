from django.shortcuts import render
from django.http import HttpResponse


def leaderboard_view(request):
    return HttpResponse("Leaderboard page - coming soon")


def friends_view(request):
    return HttpResponse("Friends page - coming soon")


def campus_war_view(request):
    return HttpResponse("Campus war page - coming soon")


def challenge_view(request, pk):
    return HttpResponse(f"Challenge {pk} page - coming soon")
