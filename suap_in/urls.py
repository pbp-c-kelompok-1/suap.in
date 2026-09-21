from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('gamification.urls')),
    path('auth/', include('authentication.urls')),
    path('scanner/', include('scanner.urls')),
    path('social/', include('social.urls')),
    path('challenge/', include('challenge.urls')),
    path('design-test/', TemplateView.as_view(template_name='test_design.html'), name='design_test'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
