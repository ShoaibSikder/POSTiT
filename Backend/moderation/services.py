from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from accounts.models import User
from audit.models import AdminAuditLog
from comments.models import Comment
from follows.models import Follow
from likes.models import Like
from notifications.models import Notification
from posts.models import Post, PostImage
from profiles.models import ProfileMedia
from search.models import SearchActivity

from common.exceptions import DomainConflict
from .models import SystemSetting


PLATFORM_LIMITS = {
    SystemSetting.Key.MAX_IMAGE_SIZE_BYTES: "POSTIT_MAX_IMAGE_SIZE_BYTES",
    SystemSetting.Key.MAX_POST_IMAGES: "POSTIT_MAX_POST_IMAGES",
    SystemSetting.Key.MAX_PROFILE_MEDIA: "POSTIT_MAX_PROFILE_MEDIA",
    SystemSetting.Key.MAX_POST_LENGTH: "POSTIT_MAX_POST_LENGTH",
    SystemSetting.Key.MAX_COMMENT_LENGTH: "POSTIT_MAX_COMMENT_LENGTH",
}
MAX_PLATFORM_LIMITS = {
    SystemSetting.Key.MAX_IMAGE_SIZE_BYTES: 50 * 1024 * 1024,
    SystemSetting.Key.MAX_POST_IMAGES: 10,
    SystemSetting.Key.MAX_PROFILE_MEDIA: 50,
    SystemSetting.Key.MAX_POST_LENGTH: 10_000,
    SystemSetting.Key.MAX_COMMENT_LENGTH: 5_000,
}


def get_platform_limit(key):
    setting_name = PLATFORM_LIMITS[key]
    default_value = getattr(settings, setting_name)
    configured = SystemSetting.objects.filter(key=key).values_list(
        "value",
        flat=True,
    ).first()
    return configured if configured is not None else default_value


def dashboard_summary():
    now = timezone.now()
    counts = {
        "users": User.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "posts": Post.objects.count(),
        "comments": Comment.objects.count(),
        "likes": Like.objects.count(),
        "follows": Follow.objects.count(),
        "post_images": PostImage.objects.count(),
        "profile_media": ProfileMedia.objects.count(),
        "notifications": Notification.objects.count(),
        "unread_notifications": Notification.objects.filter(is_read=False).count(),
        "searches_24h": SearchActivity.objects.filter(
            created_at__gte=now - timedelta(hours=24)
        ).count(),
    }
    recent_activity = AdminAuditLog.objects.select_related("admin")[:10]
    return counts, recent_activity


def deactivate_user(request, user, *, action="deactivate_user", reason=""):
    with transaction.atomic():
        if user.is_active and user.role == User.Role.ADMIN and user.is_staff:
            active_admins = User.objects.select_for_update().filter(
                role=User.Role.ADMIN,
                is_staff=True,
                is_active=True,
            )
            remaining_admins = active_admins.exclude(pk=user.pk).count()
            if not remaining_admins:
                raise DomainConflict("The last active administrator cannot be deactivated.")
        user.is_active = False
        user.save(update_fields=("is_active",))
        from audit.services import record_admin_action

        record_admin_action(
            request,
            action=action,
            target_type="user",
            target_id=user.pk,
            details={"username": user.username, "reason": reason},
        )


def activate_user(request, user, *, action="activate_user", reason=""):
    with transaction.atomic():
        if action != "unban_user" and user.is_banned:
            raise DomainConflict("Unban the account before activating it.")
        if action == "unban_user":
            user.is_banned = False
            user.is_active = True
            user.save(update_fields=("is_banned", "is_active"))
        else:
            user.is_active = True
            user.save(update_fields=("is_active",))
        from audit.services import record_admin_action

        record_admin_action(
            request,
            action=action,
            target_type="user",
            target_id=user.pk,
            details={"username": user.username, "reason": reason},
        )


def ban_user(request, user, *, reason=""):
    with transaction.atomic():
        if user.role == User.Role.ADMIN and user.is_staff and user.is_active:
            active_admins = User.objects.select_for_update().filter(
                role=User.Role.ADMIN,
                is_staff=True,
                is_active=True,
            )
            if not active_admins.exclude(pk=user.pk).exists():
                raise DomainConflict("The last active administrator cannot be banned.")
        user.is_banned = True
        user.is_active = False
        user.save(update_fields=("is_banned", "is_active"))
        from audit.services import record_admin_action

        record_admin_action(
            request,
            action="ban_user",
            target_type="user",
            target_id=user.pk,
            details={"username": user.username, "reason": reason},
        )


def remove_moderated_object(request, instance, *, target_type, reason=""):
    from audit.services import record_admin_action

    target_id = instance.pk
    with transaction.atomic():
        record_admin_action(
            request,
            action=f"remove_{target_type}",
            target_type=target_type,
            target_id=target_id,
            details={"reason": reason},
        )
        instance.delete()


def remove_profile_image(request, profile, *, image_field, reason=""):
    from audit.services import record_admin_action

    if image_field not in ("avatar", "cover_image"):
        raise ValueError("Unsupported profile image field.")
    image = getattr(profile, image_field)
    if not image:
        raise ValueError("The profile does not have this image.")
    with transaction.atomic():
        record_admin_action(
            request,
            action="remove_profile_image",
            target_type=f"profile_{image_field}",
            target_id=profile.pk,
            details={"user_id": profile.user_id, "reason": reason},
        )
        setattr(profile, image_field, "")
        profile.save(update_fields=(image_field, "updated_at"))
