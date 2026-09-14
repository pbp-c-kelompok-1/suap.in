from django.shortcuts import render
from django.http import HttpResponse


def login_view(request):
    return HttpResponse("Login page - coming soon")


def register_view(request):
    return HttpResponse("Register page - coming soon")


def logout_view(request):
    return HttpResponse("Logout page - coming soon")


def profile_view(request, username):
    return HttpResponse(f"Profile page for {username} - coming soon")
