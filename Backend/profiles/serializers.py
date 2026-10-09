from django.conf import settings
from django.db import transaction
from rest_framework import serializers

from moderation.models import SystemSetting
from moderation.services import get_platform_limit

from .models import Profile, ProfileMedia


class ProfileMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileMedia
        fields = ("id", "image", "caption", "created_at")
        read_only_fields = ("id", "created_at")


class ProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    first_name = serializers.CharField(
        source="user.first_name",
        required=False,
    )
    last_name = serializers.CharField(
        source="user.last_name",
        required=False,
    )
    follower_count = serializers.SerializerMethodField()
    following_count = serializers.SerializerMethodField()

    class Meta:
        model = Profile
        fields = (
            "id",
            "username",
            "first_name",
            "last_name",
            "bio",
            "avatar",
            "cover_image",
            "follower_count",
            "following_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "username",
            "follower_count",
            "following_count",
            "created_at",
            "updated_at",
        )

    def get_follower_count(self, instance):
        return getattr(instance.user, "follower_count", 0)

    def get_following_count(self, instance):
        return getattr(instance.user, "following_count", 0)

    def update(self, instance, validated_data):
        user_fields = validated_data.pop("user", {})
        with transaction.atomic():
            if user_fields:
                user = instance.user
                for field, value in user_fields.items():
                    setattr(user, field, value)
                user.save(update_fields=tuple(user_fields))
            for field, value in validated_data.items():
                setattr(instance, field, value)
            if validated_data:
                instance.save()
        return instance


class ProfileMediaCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProfileMedia
        fields = ("id", "image", "caption", "created_at")
        read_only_fields = ("id", "created_at")

    def create(self, validated_data):
        profile = self.context["profile"]
        with transaction.atomic():
            Profile.objects.select_for_update().get(pk=profile.pk)
            if profile.media.count() >= get_platform_limit(
                SystemSetting.Key.MAX_PROFILE_MEDIA
            ):
                raise serializers.ValidationError(
                    {
                        "image": (
                            "The profile has reached its configured media limit."
                        )
                    }
                )
            return ProfileMedia.objects.create(profile=profile, **validated_data)
