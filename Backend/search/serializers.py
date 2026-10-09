from rest_framework import serializers


class UserSearchResultSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    username = serializers.CharField(read_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    avatar = serializers.SerializerMethodField()
    follower_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)

    def get_avatar(self, user):
        image = user.profile.avatar
        return self.context["request"].build_absolute_uri(image.url) if image else None


class SearchQuerySerializer(serializers.Serializer):
    def __init__(self, *args, **kwargs):
        data = kwargs.get("data")
        if data is not None:
            data = data.copy()
            for external, internal in (("from", "from_date"), ("to", "to_date")):
                if external in data and internal not in data:
                    data[internal] = data[external]
            kwargs["data"] = data
        super().__init__(*args, **kwargs)


class UserSearchSerializer(SearchQuerySerializer):
    q = serializers.CharField(min_length=1, max_length=100, trim_whitespace=True)


class PostSearchSerializer(SearchQuerySerializer):
    q = serializers.CharField(required=False, allow_blank=True, max_length=200)
    author = serializers.CharField(required=False, max_length=150)
    from_date = serializers.DateField(required=False, input_formats=["iso-8601"])
    to_date = serializers.DateField(required=False, input_formats=["iso-8601"])

    def validate(self, attrs):
        start = attrs.get("from_date")
        end = attrs.get("to_date")
        if start and end and start > end:
            raise serializers.ValidationError(
                {"to": "The end date must be on or after the start date."}
            )
        if not any(attrs.get(key) for key in ("q", "author", "from_date", "to_date")):
            raise serializers.ValidationError(
                {"q": "Provide a search term, author, or date range."}
            )
        return attrs
