from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


class AdminAuditLog(models.Model):
    admin = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="admin_audit_events",
    )
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=50)
    target_id = models.BigIntegerField(null=True, blank=True)
    details = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-created_at", "-pk")
        indexes = [models.Index(fields=("-created_at", "admin"))]

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError("Audit records are append-only.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError("Audit records are append-only.")

