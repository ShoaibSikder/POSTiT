from rest_framework import serializers

from moderation.models import SystemSetting
from moderation.services import get_platform_limit

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    content = serializers.CharField()

    class Meta:
        model = Comment
        fields = ("id", "post", "author", "content", "created_at", "updated_at")
        read_only_fields = ("id", "post", "author", "created_at", "updated_at")

    def validate_content(self, value):
        content = value.strip()
        if not content:
            raise serializers.ValidationError("A comment cannot be blank.")
        if len(content) > get_platform_limit(SystemSetting.Key.MAX_COMMENT_LENGTH):
            raise serializers.ValidationError(
                "Comment exceeds the configured character limit."
            )
        return content
