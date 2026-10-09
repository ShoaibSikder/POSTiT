from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    actor = serializers.CharField(source="actor.username", read_only=True)

    class Meta:
        model = Notification
        fields = ("id", "actor", "type", "post", "comment", "is_read", "created_at")
        read_only_fields = fields

