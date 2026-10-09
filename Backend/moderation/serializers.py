from rest_framework import serializers

from accounts.models import User
from .models import SystemSetting
from .services import MAX_PLATFORM_LIMITS


class AdminUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "is_banned",
            "date_joined",
        )
        read_only_fields = fields


class ModerationActionSerializer(serializers.Serializer):
    reason = serializers.CharField(max_length=500, required=True, allow_blank=False)


class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = ("key", "value", "updated_by", "updated_at")
        read_only_fields = ("updated_by", "updated_at")

    def validate_key(self, value):
        if value not in SystemSetting.Key.values:
            raise serializers.ValidationError("This platform setting is not configurable.")
        return value

    def validate_value(self, value):
        if value < 1:
            raise serializers.ValidationError("The value must be a positive integer.")
        return value

    def validate(self, attrs):
        key = attrs.get("key", getattr(self.instance, "key", None))
        value = attrs.get("value")
        if key and value and value > MAX_PLATFORM_LIMITS[key]:
            raise serializers.ValidationError(
                {"value": f"The maximum supported value is {MAX_PLATFORM_LIMITS[key]}."}
            )
        return attrs
