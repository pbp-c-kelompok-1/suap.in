from datetime import timedelta

from django.utils import timezone
from django.utils.html import strip_tags
from rest_framework import serializers

from gamification import services
from gamification.models import Badge, GameProfile, UserBadge


convert_to_slug = lambda s: s.lower().replace(" ", "-")

class BadgeSerializer(serializers.ModelSerializer):
    material = serializers.SerializerMethodField()
    rarity = serializers.SerializerMethodField()

    class Meta:
        model = Badge
        fields = ['code', 'name', 'description', 'icon', 'criteria_type',
                  'threshold', 'material', 'rarity']
        read_only_fields = ['code']

    def get_material(self, obj):
        return services.badge_material_from_threshold(obj.criteria_type, obj.threshold)

    def get_rarity(self, obj):
        return services.badge_rarity(obj.criteria_type, obj.threshold)

    def validate_name(self, value):
        value = strip_tags(value).strip()
        if not value:
            raise serializers.ValidationError("Nama lencana tidak boleh kosong.")
        return value

    def validate_description(self, value):
        return strip_tags(value).strip()

    def validate_icon(self, value):
        return strip_tags(value).strip() or 'badge'

    def validate_threshold(self, value):
        if value < 1:
            raise serializers.ValidationError("Nilai harus lebih dari 0.")
        return value

    def create(self, validated_data):
        base = convert_to_slug(validated_data['name']) or 'badge'
        code = base

        n = 2
        while Badge.objects.filter(code=code).exists():
            code = f'{base}-{n}'
            n += 1
        return Badge.objects.create(code=code, **validated_data)


class GameProfileSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    # level & xp
    tier = serializers.SerializerMethodField()
    next_tier = serializers.SerializerMethodField()
    is_max_level = serializers.SerializerMethodField()
    xp_progress = serializers.SerializerMethodField()
    xp_to_next = serializers.SerializerMethodField()

    # streak
    effective_streak = serializers.SerializerMethodField()
    scanned_today = serializers.SerializerMethodField()
    next_streak_goal = serializers.SerializerMethodField()

    # freeze
    freeze_claims_remaining = serializers.SerializerMethodField()
    can_claim_freeze = serializers.SerializerMethodField()

    class Meta:
        model = GameProfile
        fields = [
            'id', 'user_id', 'username',
            'level', 'tier', 'next_tier', 'is_max_level',
            'total_xp', 'xp_progress', 'xp_to_next',
            'current_streak', 'effective_streak', 'record_streak',
            'last_activity_date', 'scanned_today', 'next_streak_goal',
            'streak_freezes', 'freeze_week_start', 'freezes_claimed_this_week',
            'freeze_claims_remaining', 'can_claim_freeze',
        ]
        read_only_fields = fields

    def get_tier(self, obj):
        return services.tier_from_level(obj.level)

    def get_next_tier(self, obj):
        nxt = services.next_tier(obj.level)
        return {'level': nxt[0], 'name': nxt[1]} if nxt else None

    def get_is_max_level(self, obj):
        return obj.level >= services.MAX_LEVEL

    def get_xp_progress(self, obj):
        return services.xp_progress(obj)

    def get_xp_to_next(self, obj):
        if obj.level >= services.MAX_LEVEL:
            return 0
        p = services.xp_progress(obj)
        return p['needed'] - p['current']

    def get_effective_streak(self, obj):
        return services.effective_streak(obj)

    def get_scanned_today(self, obj):
        return obj.last_activity_date == timezone.localdate()

    def get_next_streak_goal(self, obj):
        streak = services.effective_streak(obj)
        return next((m for m in services.STREAK_MILESTONES if m > streak),
                    services.STREAK_MILESTONES[-1])

    def _claims_remaining(self, obj):
        today = timezone.localdate()
        week_start = today - timedelta(days=today.weekday())
        claimed = obj.freezes_claimed_this_week if obj.freeze_week_start == week_start else 0
        return max(0, services.MAX_CLAIMS_PER_WEEK - claimed)

    def get_freeze_claims_remaining(self, obj):
        return self._claims_remaining(obj)

    def get_can_claim_freeze(self, obj):
        return (self._claims_remaining(obj) > 0
                and obj.streak_freezes < services.MAX_STORED_FREEZES)


class UserBadgeSerializer(serializers.ModelSerializer):
    badge = serializers.SerializerMethodField()

    class Meta:
        model = UserBadge
        fields = ['badge']
        read_only_fields = fields

    def get_badge(self, obj):
        badge = BadgeSerializer(obj.badge).data
        badge['earned_at'] = obj.earned_at.strftime("%d %b %Y")
        badge['earned_at_raw'] = obj.earned_at
        return badge