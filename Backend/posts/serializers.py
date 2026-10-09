from django.db import transaction
from rest_framework import serializers

from common.validators import validate_uploaded_image
from .models import Post, PostImage
from .validators import validate_post_content


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ("id", "image", "created_at")
        read_only_fields = fields


class PostSerializer(serializers.ModelSerializer):
    author = serializers.CharField(source="author.username", read_only=True)
    content = serializers.CharField(required=False, allow_blank=True)
    images = PostImageSerializer(many=True, read_only=True)
    likes_count = serializers.IntegerField(read_only=True, default=0)
    comments_count = serializers.IntegerField(read_only=True, default=0)
    liked_by_user = serializers.BooleanField(read_only=True, default=False)
    new_images = serializers.ListField(
        child=serializers.ImageField(validators=[validate_uploaded_image]),
        required=False,
        write_only=True,
    )
    remove_image_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        write_only=True,
    )

    class Meta:
        model = Post
        fields = (
            "id",
            "author",
            "content",
            "images",
            "likes_count",
            "comments_count",
            "liked_by_user",
            "new_images",
            "remove_image_ids",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "author", "created_at", "updated_at")

    def validate_content(self, value):
        return validate_post_content(value)

    def validate(self, attrs):
        content = attrs.get(
            "content",
            self.instance.content if self.instance else "",
        ).strip()
        new_images = attrs.get("new_images", [])
        remove_image_ids = attrs.get("remove_image_ids", [])

        if len(remove_image_ids) != len(set(remove_image_ids)):
            raise serializers.ValidationError(
                {"remove_image_ids": "An image may only be removed once."}
            )

        if self.instance is not None:
            current_image_ids = set(
                self.instance.images.values_list("pk", flat=True)
            )
            if not set(remove_image_ids).issubset(current_image_ids):
                raise serializers.ValidationError(
                    {"remove_image_ids": "One or more images do not belong to this post."}
                )
            image_count = (
                self.instance.images.count()
                - len(remove_image_ids)
                + len(new_images)
            )
        else:
            image_count = len(new_images)

        if image_count > self.max_post_images:
            raise serializers.ValidationError(
                {
                    "new_images": (
                        "The post would exceed the configured image attachment limit."
                    )
                }
            )
        if not content and image_count == 0:
            raise serializers.ValidationError(
                {"content": "A post must contain text or at least one image."}
            )
        attrs["content"] = content
        return attrs

    def create(self, validated_data):
        image_files = validated_data.pop("new_images", [])
        validated_data.pop("remove_image_ids", None)
        with transaction.atomic():
            post = Post.objects.create(
                author=self.context["request"].user,
                **validated_data,
            )
            PostImage.objects.bulk_create(
                [PostImage(post=post, image=image) for image in image_files]
            )
        return post

    def update(self, instance, validated_data):
        image_files = validated_data.pop("new_images", [])
        remove_image_ids = validated_data.pop("remove_image_ids", [])
        with transaction.atomic():
            post = Post.objects.select_for_update().get(pk=instance.pk)
            current_image_count = post.images.count()
            if (
                current_image_count
                - len(remove_image_ids)
                + len(image_files)
                > self.max_post_images
            ):
                raise serializers.ValidationError(
                    {
                        "new_images": (
                            "The post would exceed the configured image attachment limit."
                        )
                    }
                )
            if remove_image_ids:
                post.images.filter(pk__in=remove_image_ids).delete()
            for field, value in validated_data.items():
                setattr(post, field, value)
            post.save()
            PostImage.objects.bulk_create(
                [PostImage(post=post, image=image) for image in image_files]
            )
        return post

    def to_internal_value(self, data):
        if hasattr(data, "getlist"):
            payload = data.dict()
            uploads = data.getlist("images")
            if uploads:
                payload["new_images"] = uploads
            remove_ids = data.getlist("remove_image_ids")
            remove_ids.extend(data.getlist("remove_image_ids[]"))
            if remove_ids:
                payload["remove_image_ids"] = [
                    item
                    for value in remove_ids
                    for item in str(value).split(",")
                    if item
                ]
            data = payload
        elif isinstance(data, dict) and "images" in data:
            data = {**data, "new_images": data["images"]}
            data.pop("images")
        return super().to_internal_value(data)

    @property
    def max_post_images(self):
        from moderation.models import SystemSetting
        from moderation.services import get_platform_limit

        return get_platform_limit(SystemSetting.Key.MAX_POST_IMAGES)
