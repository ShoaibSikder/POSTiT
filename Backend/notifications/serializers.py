from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source="actor.username", read_only=True)
    actor_avatar = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = (
            "id",
            "actor",
            "actor_avatar",
            "type",
            "post",
            "comment",
            "is_read",
            "created_at",
        )
        read_only_fields = fields

    def get_actor_avatar(self, instance):
        if not instance.actor_id:
            return None
        avatar = instance.actor.profile.avatar
        if not avatar:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(avatar.url) if request else avatar.url
