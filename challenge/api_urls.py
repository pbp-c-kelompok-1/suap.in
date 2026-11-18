from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .api_views import (
    ClaimQuestAPIView,
    DailyQuestAPIView,
    NotificationViewSet,
    WeeklyReportViewSet,
)

router = DefaultRouter()
router.register('notifications', NotificationViewSet, basename='notification')
router.register('reports', WeeklyReportViewSet, basename='report')

urlpatterns = [
    path('daily/', DailyQuestAPIView.as_view(), name='api-daily'),
    path('daily/<str:quest_id>/claim/', ClaimQuestAPIView.as_view(), name='api-daily-claim'),
    path('', include(router.urls)),
]
