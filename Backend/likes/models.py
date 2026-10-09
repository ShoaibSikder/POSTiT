from django.conf import settings
from django.db import models

from posts.models import Post


class Like(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="likes",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="post_likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("post", "user"),
                name="likes_unique_post_like",
            )
        ]
        indexes = [
            models.Index(
                fields=("user", "created_at"),
                name="likes_user_date_idx",
            ),
        ]

    def __str__(self):
        return f"Like by {self.user.username} on post {self.post_id}"
