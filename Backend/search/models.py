from django.conf import settings
from django.db import models


class SearchActivity(models.Model):
    class SearchType(models.TextChoices):
        USERS = "users", "Users"
        POSTS = "posts", "Posts"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="search_activity",
    )
    search_type = models.CharField(max_length=10, choices=SearchType.choices)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        indexes = [models.Index(fields=("search_type", "-created_at"))]

