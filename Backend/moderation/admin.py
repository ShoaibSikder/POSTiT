from django import forms
from django.contrib import admin

from audit.services import record_admin_action

from .models import SystemSetting
from .services import MAX_PLATFORM_LIMITS


class SystemSettingAdminForm(forms.ModelForm):
    class Meta:
        model = SystemSetting
        fields = ("key", "value")

    def clean(self):
        cleaned_data = super().clean()
        key = cleaned_data.get("key")
        value = cleaned_data.get("value")
        if key and value is not None and value > MAX_PLATFORM_LIMITS[key]:
            self.add_error(
                "value",
                f"The maximum supported value is {MAX_PLATFORM_LIMITS[key]}.",
            )
        return cleaned_data


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    form = SystemSettingAdminForm
    list_display = ("key", "value", "updated_by", "updated_at")
    list_filter = ("key",)
    search_fields = ("key",)
    readonly_fields = ("updated_by", "updated_at")

    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
        record_admin_action(
            request,
            action="update_system_setting",
            target_type="system_setting",
            target_id=obj.pk,
            details={
                "key": obj.key,
                "value": obj.value,
                "created": not change,
            },
        )

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
