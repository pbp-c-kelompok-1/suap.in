"""
URL configuration for suap_in project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]

# TODO (post-Checkpoint 1): restore full routing below once the rocket page
# requirement is no longer needed for deployment.
#
# from django.urls import include
# from django.conf import settings
# from django.conf.urls.static import static
#
# urlpatterns = [
#     path('admin/', admin.site.urls),
#     path('', include('gamification.urls')),  # home = gamification dashboard
#     path('auth/', include('authentication.urls')),
#     path('scanner/', include('scanner.urls')),
#     path('social/', include('social.urls')),
#     path('challenge/', include('challenge.urls')),
# ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
