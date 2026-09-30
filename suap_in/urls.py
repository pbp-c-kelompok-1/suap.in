from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('story/', include('story.urls')),
    path('', include('gamification.urls')),
    path('auth/', include('authentication.urls')),
    path('scanner/', include('scanner.urls')),
    path('social/', include('social.urls')),
    path('challenge/', include('challenge.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
