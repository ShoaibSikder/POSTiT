from rest_framework import serializers

from moderation.models import SystemSetting
from moderation.services import get_platform_limit

from .models import Comment


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    author_avatar = serializers.SerializerMethodField()
    content = serializers.CharField()

    class Meta:
        model = Comment
        fields = (
            "id",
            "post",
            "author",
            "author_avatar",
            "content",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "post",
            "author",
            "author_avatar",
            "created_at",
            "updated_at",
        )

    def get_author_avatar(self, instance):
        avatar = instance.author.profile.avatar
        if not avatar:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(avatar.url) if request else avatar.url

    def validate_content(self, value):
        content = value.strip()
        if not content:
            raise serializers.ValidationError("A comment cannot be blank.")
        if len(content) > get_platform_limit(SystemSetting.Key.MAX_COMMENT_LENGTH):
            raise serializers.ValidationError(
                "Comment exceeds the configured character limit."
            )
        return content
