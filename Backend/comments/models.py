from django.conf import settings
from django.db import models

from posts.models import Post


class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    content = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("created_at", "pk")
        indexes = [
            models.Index(
                fields=("post", "created_at"),
                name="comments_post_date_idx",
            ),
            models.Index(
                fields=("author", "created_at"),
                name="comments_author_date_idx",
            ),
        ]

    def __str__(self):
        return f"Comment {self.pk} by {self.author.username}"
