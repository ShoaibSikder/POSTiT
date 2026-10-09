from django.contrib import admin

from .models import SystemSetting


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "updated_by", "updated_at")
    readonly_fields = ("key", "value", "updated_by", "updated_at")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

