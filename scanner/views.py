from django.shortcuts import render
from django.http import HttpResponse, JsonResponse


def scan_view(request):
    return HttpResponse("Scan page - coming soon")


def daily_log_view(request):
    return HttpResponse("Daily log page - coming soon")


def api_scan(request):
    return JsonResponse({"status": "coming soon"})
