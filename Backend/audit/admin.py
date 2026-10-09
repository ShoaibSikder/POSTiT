from django.contrib import admin

from .models import AdminAuditLog


@admin.register(AdminAuditLog)
class AdminAuditLogAdmin(admin.ModelAdmin):
    list_display = ("id", "admin", "action", "target_type", "target_id", "created_at")
    list_filter = ("action", "target_type", "created_at")
    search_fields = ("admin__username", "action", "target_type")
    readonly_fields = (
        "admin",
        "action",
        "target_type",
        "target_id",
        "details",
        "ip_address",
        "created_at",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

