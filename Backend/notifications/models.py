from django.conf import settings
from django.db import models

from comments.models import Comment
from posts.models import Post


class Notification(models.Model):
    class Type(models.TextChoices):
        FOLLOW = "follow", "Follow"
        LIKE = "like", "Like"
        COMMENT = "comment", "Comment"

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="sent_notifications",
    )
    type = models.CharField(max_length=10, choices=Type.choices)
    post = models.ForeignKey(
        Post,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    comment = models.ForeignKey(
        Comment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notifications",
    )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        indexes = [
            models.Index(fields=("recipient", "is_read", "-created_at")),
        ]

