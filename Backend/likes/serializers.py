from rest_framework import serializers


class LikeStatusSerializer(serializers.Serializer):
    liked = serializers.BooleanField()
    likes_count = serializers.IntegerField(min_value=0)
