from django.contrib import admin

from .models import Profile, ProfileMedia


class ProfileMediaInline(admin.TabularInline):
    model = ProfileMedia
    extra = 0
    readonly_fields = ("created_at",)


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "updated_at")
    search_fields = ("user__username", "user__email", "bio")
    readonly_fields = ("created_at", "updated_at")
    inlines = (ProfileMediaInline,)


@admin.register(ProfileMedia)
class ProfileMediaAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "caption", "created_at")
    search_fields = ("profile__user__username", "caption")
    readonly_fields = ("created_at",)

