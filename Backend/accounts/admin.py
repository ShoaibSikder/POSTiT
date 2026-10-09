from django import forms
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.helpers import ActionForm
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from common.exceptions import DomainConflict
from moderation.services import activate_user, ban_user, deactivate_user

from .models import User


class UserModerationActionForm(ActionForm):
    reason = forms.CharField(
        required=False,
        max_length=500,
        help_text="Required for account moderation actions.",
    )


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    action_form = UserModerationActionForm
    actions = (
        "ban_selected_users",
        "unban_selected_users",
        "deactivate_selected_users",
        "activate_selected_users",
    )
    list_display = (
        "username",
        "email",
        "role",
        "is_active",
        "is_banned",
        "is_staff",
    )
    list_filter = ("role", "is_active", "is_banned", "is_staff")
    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("username",)
    readonly_fields = ("last_login", "date_joined", "is_active", "is_banned")
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("POSTiT access", {"fields": ("role", "is_banned")}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ("POSTiT access", {"fields": ("email", "role")}),
    )

    def _moderate_selected_users(self, request, queryset, action):
        reason = request.POST.get("reason", "").strip()
        if not reason:
            self.message_user(
                request,
                "Enter a reason in the Reason field before applying this action.",
                level=messages.ERROR,
            )
            return

        succeeded = 0
        failures = []
        for user in queryset.iterator():
            try:
                if action == "ban":
                    ban_user(request, user, reason=reason)
                elif action == "unban":
                    if not user.is_banned:
                        raise ValueError("This account is not banned.")
                    activate_user(
                        request,
                        user,
                        action="unban_user",
                        reason=reason,
                    )
                elif action == "deactivate":
                    deactivate_user(request, user, reason=reason)
                else:
                    if user.is_banned:
                        raise ValueError("Unban the account before activating it.")
                    activate_user(request, user, reason=reason)
                succeeded += 1
            except (DomainConflict, ValueError) as exc:
                failures.append(f"{user.username}: {exc}")

        if succeeded:
            self.message_user(
                request,
                f"{action.title()} completed for {succeeded} account(s).",
                level=messages.SUCCESS,
            )
        for failure in failures:
            self.message_user(request, failure, level=messages.WARNING)

    @admin.action(description="Ban selected accounts")
    def ban_selected_users(self, request, queryset):
        self._moderate_selected_users(request, queryset, "ban")

    @admin.action(description="Unban selected accounts")
    def unban_selected_users(self, request, queryset):
        self._moderate_selected_users(request, queryset, "unban")

    @admin.action(description="Deactivate selected accounts")
    def deactivate_selected_users(self, request, queryset):
        self._moderate_selected_users(request, queryset, "deactivate")

    @admin.action(description="Activate selected accounts")
    def activate_selected_users(self, request, queryset):
        self._moderate_selected_users(request, queryset, "activate")
