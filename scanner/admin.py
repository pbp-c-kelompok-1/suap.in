from django.contrib import admin
from .models import FoodItem, FoodLog, CarbonBudget


@admin.register(FoodItem)
class FoodItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'co2_per_serving_grams', 'is_indonesian']
    list_filter = ['category', 'is_indonesian']
    search_fields = ['name', 'name_en']


@admin.register(FoodLog)
class FoodLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'custom_name', 'co2_grams', 'scanned_at']
    list_filter = ['scanned_at']


@admin.register(CarbonBudget)
class CarbonBudgetAdmin(admin.ModelAdmin):
    list_display = ['user', 'date', 'budget_grams', 'used_grams']
