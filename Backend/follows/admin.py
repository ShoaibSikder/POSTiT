from django.contrib import admin

from .models import Follow


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ("id", "follower", "following", "created_at")
    list_filter = ("created_at",)
    search_fields = ("follower__username", "following__username")
    readonly_fields = ("created_at",)
