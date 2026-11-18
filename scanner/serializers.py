from rest_framework import serializers
from .models import FoodItem, FoodLog, CarbonBudget


class FoodItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = FoodItem
        fields = ['id', 'name', 'name_en', 'category', 'co2_per_serving_grams', 'serving_size_description', 'is_indonesian']


class FoodLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)
    food_name = serializers.SerializerMethodField()

    class Meta:
        model = FoodLog
        fields = ['id', 'username', 'food_name', 'custom_name', 'co2_grams', 'scanned_at', 'notes']

    def get_food_name(self, obj):
        return obj.custom_name or (obj.food_item.name if obj.food_item else 'Item')


class CarbonBudgetSerializer(serializers.ModelSerializer):
    remaining_grams = serializers.FloatField(read_only=True)
    percentage_used = serializers.FloatField(read_only=True)

    class Meta:
        model = CarbonBudget
        fields = ['id', 'date', 'budget_grams', 'used_grams', 'remaining_grams', 'percentage_used']
