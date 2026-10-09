from rest_framework import serializers

from .models import AdminAuditLog


class AdminAuditLogSerializer(serializers.ModelSerializer):
    admin = serializers.CharField(source="admin.username", read_only=True)

    class Meta:
        model = AdminAuditLog
        fields = (
            "id",
            "admin",
            "action",
            "target_type",
            "target_id",
            "details",
            "ip_address",
            "created_at",
        )
        read_only_fields = fields

