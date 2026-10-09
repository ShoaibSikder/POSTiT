from rest_framework import serializers

from posts.serializers import PostSerializer


class FeedPostSerializer(PostSerializer):
    is_own_post = serializers.SerializerMethodField()

    class Meta(PostSerializer.Meta):
        fields = PostSerializer.Meta.fields + ("is_own_post",)

    def get_is_own_post(self, post):
        request = self.context.get("request")
        return bool(
            request
            and request.user.is_authenticated
            and post.author_id == request.user.pk
        )

