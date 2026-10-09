from django.conf import settings
from django.db import models
from django.db.models import F, Q


class Follow(models.Model):
    follower = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="following_relationships",
    )
    following = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="follower_relationships",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=("follower", "following"),
                name="follows_unique_relationship",
            ),
            models.CheckConstraint(
                condition=~Q(follower=F("following")),
                name="follows_no_self_follow",
            ),
        ]
        indexes = [
            models.Index(
                fields=("following", "created_at"),
                name="follows_target_date_idx",
            ),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"
