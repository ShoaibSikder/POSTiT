from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    class Role(models.TextChoices):
        USER = "user", "User"
        ADMIN = "admin", "Administrator"

    email = models.EmailField("email address", unique=True)
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
    )
    is_banned = models.BooleanField(default=False)

    objects = UserManager()

    REQUIRED_FIELDS = ["email"]

    def save(self, *args, **kwargs):
        self.username = self.normalize_username(self.username).strip().lower()
        self.email = (
            self.__class__.objects.normalize_email(self.email).strip().lower()
        )
        return super().save(*args, **kwargs)
