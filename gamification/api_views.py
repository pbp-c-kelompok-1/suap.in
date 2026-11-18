from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from gamification import serializers, services, permissions
from gamification.models import Badge, UserBadge


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_game_profile(request):
    profile = services.get_profile(request.user)
    return Response(serializers.GameProfileSerializer(profile).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_badges_list(request):
    services.check_badges(request.user)

    unlocked = UserBadge.objects.filter(user=request.user).select_related('badge', 'user')
    locked = Badge.objects.exclude(id__in=unlocked.values_list('badge_id', flat=True))

    criteria = request.query_params.get('criteria_type')
    if criteria:
        unlocked = unlocked.filter(badge__criteria_type=criteria)
        locked = locked.filter(criteria_type=criteria)

    unlocked_data = serializers.UserBadgeSerializer(unlocked, many=True).data
    locked_data = serializers.BadgeSerializer(locked, many=True).data

    return Response({
        'unlocked': unlocked_data,
        'locked': locked_data,
        'owned_count': len(unlocked_data),
        'total_count': len(unlocked_data) + len(locked_data),
    })


@api_view(['GET', 'POST'])
@permission_classes([permissions.IsGamificationStaffOrReadOnly])
def badge_list(request):
    if request.method == 'POST':
        serializer = serializers.BadgeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    badges = Badge.objects.all().order_by('criteria_type', 'threshold', 'name')
    
    name_query = request.query_params.get('name', '').strip()
    criteria_query = request.query_params.get('criteria_type', '').strip()
    if name_query:
        badges = badges.filter(name__icontains=name_query)
    if criteria_query:
        badges = badges.filter(criteria_type__icontains=criteria_query)
            
    serializer = serializers.BadgeSerializer(badges, many=True, context={"request": request})
    return Response(serializer.data)


@api_view(['GET', 'HEAD', 'DELETE'])
@permission_classes([permissions.IsGamificationStaffOrReadOnly])
def badge_detail(request, code):
    badge = get_object_or_404(Badge, code=code)
    if request.method in ('GET', 'HEAD'):
        serializer = serializers.BadgeSerializer(badge, context={"request": request})
        return Response(serializer.data)

    badge.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)