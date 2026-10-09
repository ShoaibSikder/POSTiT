from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class SystemSetting(models.Model):
    class Key(models.TextChoices):
        MAX_IMAGE_SIZE_BYTES = "POSTIT_MAX_IMAGE_SIZE_BYTES", "Maximum image size"
        MAX_POST_IMAGES = "POSTIT_MAX_POST_IMAGES", "Maximum post images"
        MAX_PROFILE_MEDIA = "POSTIT_MAX_PROFILE_MEDIA", "Maximum profile media"
        MAX_POST_LENGTH = "POSTIT_MAX_POST_LENGTH", "Maximum post length"
        MAX_COMMENT_LENGTH = "POSTIT_MAX_COMMENT_LENGTH", "Maximum comment length"

    key = models.CharField(max_length=40, choices=Key.choices, unique=True)
    value = models.PositiveIntegerField()
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="updated_platform_settings",
    )
    updated_at = models.DateTimeField(auto_now=True)

    def clean(self):
        if self.value < 1:
            raise ValidationError({"value": "The value must be a positive integer."})

    def __str__(self):
        return self.get_key_display()

