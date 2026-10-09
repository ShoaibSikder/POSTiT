from rest_framework import serializers

from moderation.models import SystemSetting
from moderation.services import get_platform_limit


def validate_post_content(value):
    content = value.strip()
    if len(content) > get_platform_limit(SystemSetting.Key.MAX_POST_LENGTH):
        raise serializers.ValidationError(
            "Post content exceeds the configured character limit."
        )
    return content

