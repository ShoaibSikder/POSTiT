from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("id", "recipient", "actor", "type", "is_read", "created_at")
    list_filter = ("type", "is_read", "created_at")
    search_fields = ("recipient__username", "actor__username")
    readonly_fields = ("recipient", "actor", "type", "post", "comment", "created_at")

