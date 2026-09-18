from django.db import models
from django.contrib.auth.models import User


class FoodItem(models.Model):
    """Master database of food items and their carbon footprint values."""
    name = models.CharField(max_length=200)
    name_en = models.CharField(max_length=200, blank=True)
    category = models.CharField(max_length=100)
    co2_per_serving_grams = models.FloatField(help_text="CO2 in grams per standard serving")
    serving_size_description = models.CharField(max_length=100, default="1 porsi sedang")
    source = models.CharField(max_length=200, default="FAO / OurWorldInData")
    is_indonesian = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.co2_per_serving_grams}g CO2)"

    class Meta:
        ordering = ['category', 'name']


class FoodLog(models.Model):
    """Log of food scanned by user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='food_logs')
    food_item = models.ForeignKey(FoodItem, on_delete=models.SET_NULL, null=True, blank=True)
    custom_name = models.CharField(max_length=200, blank=True)
    co2_grams = models.FloatField()
    photo = models.ImageField(upload_to='food_scans/', null=True, blank=True)
    ai_raw_response = models.TextField(blank=True)
    scanned_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.custom_name or self.food_item} - {self.scanned_at.date()}"

    class Meta:
        ordering = ['-scanned_at']


class CarbonBudget(models.Model):
    """Daily carbon budget per user."""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carbon_budgets')
    date = models.DateField()
    budget_grams = models.FloatField(default=2000.0)
    used_grams = models.FloatField(default=0.0)

    @property
    def remaining_grams(self):
        return self.budget_grams - self.used_grams

    @property
    def percentage_used(self):
        return (self.used_grams / self.budget_grams) * 100

    def __str__(self):
        return f"{self.user.username} - {self.date} - {self.used_grams}/{self.budget_grams}g"

    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
