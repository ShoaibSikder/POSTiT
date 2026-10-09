import uuid
from pathlib import Path

from django.conf import settings
from django.db import models
from django.utils import timezone

from common.validators import validate_uploaded_image


def profile_image_upload_to(instance, filename):
    extension = Path(filename).suffix.lower()
    return f"profiles/{timezone.now():%Y/%m}/{uuid.uuid4().hex}{extension}"


class Profile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    bio = models.CharField(max_length=500, blank=True)
    avatar = models.ImageField(
        upload_to=profile_image_upload_to,
        blank=True,
        validators=[validate_uploaded_image],
    )
    cover_image = models.ImageField(
        upload_to=profile_image_upload_to,
        blank=True,
        validators=[validate_uploaded_image],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile for {self.user.username}"


class ProfileMedia(models.Model):
    profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        related_name="media",
    )
    image = models.ImageField(
        upload_to=profile_image_upload_to,
        validators=[validate_uploaded_image],
    )
    caption = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-pk")

    def __str__(self):
        return f"Profile media for {self.profile.user.username}"
