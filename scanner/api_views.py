from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.utils import timezone

from .models import FoodItem, FoodLog, CarbonBudget
from .serializers import FoodItemSerializer, FoodLogSerializer, CarbonBudgetSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def api_food_items(request):
    items = FoodItem.objects.all()
    serializer = FoodItemSerializer(items, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_food_logs(request):
    if request.user.is_authenticated:
        logs = FoodLog.objects.filter(user=request.user)
    else:
        logs = FoodLog.objects.all()[:10]
    serializer = FoodLogSerializer(logs, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def api_carbon_budget(request):
    today = timezone.localdate()
    if request.user.is_authenticated:
        budget, _ = CarbonBudget.objects.get_or_create(
            user=request.user,
            date=today,
            defaults={'budget_grams': 2000.0, 'used_grams': 0.0}
        )
        serializer = CarbonBudgetSerializer(budget)
        return Response(serializer.data)
    return Response({
        'date': str(today),
        'budget_grams': 2000.0,
        'used_grams': 0.0,
        'remaining_grams': 2000.0,
        'percentage_used': 0.0
    })
