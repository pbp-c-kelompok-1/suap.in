from django.shortcuts import render
from django.http import HttpResponse


def dashboard_view(request):
    return render(request, 'gamification/dashboard.html')


def streak_view(request):
    return HttpResponse("Streak page - coming soon")


def level_view(request):
    return HttpResponse("Level page - coming soon")


def story_view(request):
    return HttpResponse("Story page - coming soon")
