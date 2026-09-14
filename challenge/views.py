from django.shortcuts import render
from django.http import HttpResponse, JsonResponse


def challenge_list_view(request):
    return HttpResponse("Challenge list page - coming soon")


def weekly_report_view(request):
    return HttpResponse("Weekly report page - coming soon")


def api_daily_challenges(request):
    return JsonResponse({"status": "coming soon"})
