from rest_framework import serializers

from .models import Notification, WeeklyReport


class QuestSerializer(serializers.Serializer):
    """Misi harian. Sumbernya dict dari todays_quests(), bukan model."""
    id = serializers.CharField()
    title = serializers.CharField()
    desc = serializers.CharField()
    why = serializers.CharField(required=False)
    goal = serializers.IntegerField()
    val = serializers.IntegerField()
    xp = serializers.IntegerField()
    tone = serializers.CharField()
    icon = serializers.CharField()
    failed = serializers.BooleanField()
    claimed = serializers.BooleanField(default=False)
    done = serializers.SerializerMethodField()

    def get_done(self, quest):
        return quest['val'] >= quest['goal']


class NotificationSerializer(serializers.ModelSerializer):
    is_read = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = ['id', 'key', 'kind', 'icon', 'tone', 'title', 'body',
                  'link', 'is_read', 'created_at']
        read_only_fields = fields

    def get_is_read(self, obj):
        return obj.read_at is not None


class WeeklyReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = WeeklyReport
        fields = ['id', 'week_start', 'week_end', 'total_co2_grams',
                  'days_logged', 'scans', 'average_daily_grams',
                  'projection_annual_kg', 'rank_national', 'rank_campus',
                  'data']
        read_only_fields = fields
