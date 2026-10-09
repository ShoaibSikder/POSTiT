from django.contrib import admin

from .models import Like


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ("id", "post", "user", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username",)
    readonly_fields = ("created_at",)
