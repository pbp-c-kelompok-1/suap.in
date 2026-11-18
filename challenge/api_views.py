from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from gamification import services as game

from .models import Notification, QuestClaim, WeeklyReport
from .serializers import (
    NotificationSerializer,
    QuestSerializer,
    WeeklyReportSerializer,
)
from .services import DEFAULT_QUEST_XP, todays_quests

# Izin & autentikasi default diatur di REST_FRAMEWORK (settings.py):
# semua endpoint di sini wajib login.


class DailyQuestAPIView(APIView):
    """GET /api/challenge/daily/ -> 3 misi harian + progres + status klaim."""

    def get(self, request):
        today = timezone.localdate()
        quests, scans_today, used_grams, budget_grams = todays_quests(request.user, today)

        claimed_ids = set(
            QuestClaim.objects.filter(user=request.user, date=today)
            .values_list('quest_id', flat=True)
        )
        for q in quests:
            q['claimed'] = q['id'] in claimed_ids

        return Response({
            'date': today.isoformat(),
            'scans_today': scans_today,
            'used_grams': used_grams,
            'budget_grams': budget_grams,
            'quests': QuestSerializer(quests, many=True).data,
        })


class ClaimQuestAPIView(APIView):
    """POST /api/challenge/daily/<quest_id>/claim/ -> klaim XP misi yang selesai."""

    def post(self, request, quest_id):
        today = timezone.localdate()
        quests, _, _, _ = todays_quests(request.user, today)
        quest = next((q for q in quests if q['id'] == quest_id), None)

        if quest is None:
            return Response({'detail': 'Misi tidak ditemukan.'},
                            status=status.HTTP_404_NOT_FOUND)
        if quest['val'] < quest['goal']:
            return Response({'detail': 'Misi ini belum selesai.'},
                            status=status.HTTP_400_BAD_REQUEST)

        xp = quest.get('xp', DEFAULT_QUEST_XP)
        try:
            with transaction.atomic():
                QuestClaim.objects.create(user=request.user, date=today,
                                          quest_id=quest_id, xp=xp)
                result = game.award_xp(request.user, xp)
        except IntegrityError:
            return Response({'detail': 'Hadiah misi ini sudah diklaim.'},
                            status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'quest_id': quest_id,
            'xp': xp,
            'level': result['level'],
            'leveled_up': result['leveled_up'],
        }, status=status.HTTP_201_CREATED)


class NotificationViewSet(mixins.ListModelMixin,
                          mixins.RetrieveModelMixin,
                          mixins.DestroyModelMixin,
                          viewsets.GenericViewSet):
    """
    GET    /api/challenge/notifications/            daftar notifikasi
    GET    /api/challenge/notifications/<id>/       detail
    DELETE /api/challenge/notifications/<id>/       hapus (soft: dismissed=True)
    POST   /api/challenge/notifications/<id>/read/  tandai dibaca
    POST   /api/challenge/notifications/read-all/   tandai semua dibaca
    """
    serializer_class = NotificationSerializer

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user, dismissed=False)

    def perform_destroy(self, instance):
        # Sama seperti di web: barisnya tetap ada supaya tidak muncul lagi.
        instance.dismissed = True
        instance.save(update_fields=['dismissed'])

    @action(detail=True, methods=['post'])
    def read(self, request, pk=None):
        notif = self.get_object()
        if notif.read_at is None:
            notif.read_at = timezone.now()
            notif.save(update_fields=['read_at'])
        return Response(self.get_serializer(notif).data)

    @action(detail=False, methods=['post'], url_path='read-all')
    def read_all(self, request):
        updated = self.get_queryset().filter(read_at__isnull=True).update(read_at=timezone.now())
        return Response({'updated': updated})


class WeeklyReportViewSet(viewsets.ReadOnlyModelViewSet):
    """GET /api/challenge/reports/ dan /api/challenge/reports/<id>/ (hanya milik sendiri)."""
    serializer_class = WeeklyReportSerializer

    def get_queryset(self):
        return WeeklyReport.objects.filter(user=self.request.user)
