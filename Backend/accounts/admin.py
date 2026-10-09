from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_staff",
    )
    list_filter = ("role", "is_active", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Postit access", {"fields": ("role",)}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("Postit access", {"fields": ("email", "role")}),
    )
