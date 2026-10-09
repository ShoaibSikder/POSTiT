import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.validators import validate_uploaded_image


def post_image_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"posts/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{extension}"


class Post(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    content = models.TextField(max_length=2000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        indexes = [
            models.Index(fields=("-created_at", "-id"), name="posts_feed_order_idx"),
            models.Index(fields=("author", "-created_at"), name="posts_author_date_idx"),
        ]

    def __str__(self):
        return f"Post {self.pk} by {self.author.username}"


class PostImage(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="images",
    )
    image = models.ImageField(
        upload_to=post_image_upload_to,
        validators=[validate_uploaded_image],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "pk")

    def __str__(self):
        return f"Image for post {self.post_id}"
