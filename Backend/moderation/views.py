from django.db.models import Q
from django.shortcuts import get_object_or_404
from datetime import timedelta

from django.db.models import Count
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from audit.models import AdminAuditLog
from audit.services import record_admin_action
from audit.serializers import AdminAuditLogSerializer
from comments.models import Comment
from comments.serializers import CommentSerializer
from follows.models import Follow
from likes.models import Like
from notifications.models import Notification
from notifications.serializers import NotificationSerializer
from posts.models import Post, PostImage
from posts.serializers import PostSerializer
from profiles.models import Profile, ProfileMedia
from search.models import SearchActivity
from common.pagination import StandardResultsPagination
from posts.services import posts_with_engagement

from .models import SystemSetting
from .permissions import IsPlatformAdmin
from .serializers import (
    AdminUserSerializer,
    ModerationActionSerializer,
    SystemSettingSerializer,
)
from .services import (
    activate_user,
    ban_user,
    dashboard_summary,
    deactivate_user,
    remove_moderated_object,
    remove_profile_image,
)


class AdminEndpoint(APIView):
    permission_classes = (IsAuthenticated, IsPlatformAdmin)


class AdminDashboardView(AdminEndpoint):
    def get(self, request):
        counts, recent = dashboard_summary()
        activity = [
            {
                "id": item.pk,
                "admin": item.admin.username,
                "action": item.action,
                "target_type": item.target_type,
                "target_id": item.target_id,
                "created_at": item.created_at,
            }
            for item in recent
        ]
        return Response({"counts": counts, "recent_admin_activity": activity})


class AdminUserListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsPlatformAdmin)
    serializer_class = AdminUserSerializer

    def get_queryset(self):
        queryset = User.objects.all().order_by("username")
        term = self.request.query_params.get("q", "").strip()
        active = self.request.query_params.get("is_active")
        account_status = self.request.query_params.get("status")
        if term:
            queryset = queryset.filter(
                Q(username__icontains=term)
                | Q(email__icontains=term)
                | Q(first_name__icontains=term)
                | Q(last_name__icontains=term)
            )
        if active is not None:
            if active.lower() not in ("true", "false"):
                raise ValidationError({"is_active": "Use true or false."})
            queryset = queryset.filter(is_active=active.lower() == "true")
        if account_status:
            status_filters = {
                "active": Q(is_active=True, is_banned=False),
                "inactive": Q(is_active=False, is_banned=False),
                "banned": Q(is_banned=True),
            }
            condition = status_filters.get(account_status.lower())
            if condition is None:
                raise ValidationError(
                    {"status": "Choose active, inactive, or banned."}
                )
            queryset = queryset.filter(condition)
        return queryset


class AdminUserActionView(AdminEndpoint):
    def post(self, request, pk, action):
        user = get_object_or_404(User, pk=pk)
        serializer = ModerationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"].strip()
        if not reason:
            raise ValidationError({"reason": "Provide a short reason."})
        try:
            if action == "ban":
                ban_user(request, user, reason=reason)
            elif action == "unban":
                if not user.is_banned:
                    raise ValidationError({"detail": "This account is not banned."})
                activate_user(request, user, action="unban_user", reason=reason)
            elif action == "deactivate":
                deactivate_user(request, user, reason=reason)
            elif action == "activate":
                activate_user(request, user, reason=reason)
            else:
                raise ValidationError({"detail": "Unknown account action."})
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        user.refresh_from_db()
        return Response(AdminUserSerializer(user).data)


class AdminPostListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsPlatformAdmin)
    serializer_class = PostSerializer
    queryset = (
        Post.objects.select_related("author")
        .prefetch_related("images")
        .order_by("-created_at")
    )

    def get_queryset(self):
        return posts_with_engagement(self.queryset.all(), self.request.user)


class AdminPostDeleteView(AdminEndpoint):
    def delete(self, request, pk):
        serializer = ModerationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        post = get_object_or_404(Post, pk=pk)
        remove_moderated_object(
            request,
            post,
            target_type="post",
            reason=serializer.validated_data["reason"].strip(),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminCommentListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsPlatformAdmin)
    serializer_class = CommentSerializer
    queryset = Comment.objects.select_related("author", "post").order_by("-created_at")


class AdminCommentDeleteView(AdminEndpoint):
    def delete(self, request, pk):
        serializer = ModerationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        comment = get_object_or_404(Comment, pk=pk)
        remove_moderated_object(
            request,
            comment,
            target_type="comment",
            reason=serializer.validated_data["reason"].strip(),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMediaDeleteView(AdminEndpoint):
    def delete(self, request, media_type, pk):
        serializer = ModerationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data["reason"].strip()
        if not reason:
            raise ValidationError({"reason": "Provide a short reason."})
        models = {
            "post": PostImage,
            "profile": ProfileMedia,
        }
        model = models.get(media_type)
        if media_type in ("avatar", "cover"):
            profile = get_object_or_404(Profile, pk=pk)
            try:
                remove_profile_image(
                    request,
                    profile,
                    image_field="avatar" if media_type == "avatar" else "cover_image",
                    reason=reason,
                )
            except ValueError as exc:
                raise ValidationError({"detail": str(exc)}) from exc
            return Response(status=status.HTTP_204_NO_CONTENT)
        if model is None:
            raise ValidationError({"media_type": "Choose post, profile, avatar, or cover."})
        media = get_object_or_404(model, pk=pk)
        remove_moderated_object(
            request,
            media,
            target_type=f"{media_type}_media",
            reason=reason,
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMediaListView(generics.GenericAPIView):
    permission_classes = (IsAuthenticated, IsPlatformAdmin)
    pagination_class = StandardResultsPagination

    def get(self, request, media_type):
        if media_type == "post":
            items = PostImage.objects.select_related(
                "post",
                "post__author",
            ).order_by("-created_at", "-pk")
        elif media_type == "profile":
            items = ProfileMedia.objects.select_related(
                "profile",
                "profile__user",
            ).order_by("-created_at", "-pk")
        else:
            raise ValidationError({"media_type": "Choose post or profile."})

        page = self.paginate_queryset(items)
        results = []
        for item in page:
            image = item.image
            if media_type == "post":
                result = {
                    "id": item.pk,
                    "media_type": media_type,
                    "owner": item.post.author.username,
                    "post_id": item.post_id,
                }
            else:
                result = {
                    "id": item.pk,
                    "media_type": media_type,
                    "owner": item.profile.user.username,
                    "caption": item.caption,
                }
            result["url"] = request.build_absolute_uri(image.url)
            result["created_at"] = item.created_at
            results.append(result)
        return self.get_paginated_response(results)


class AdminNotificationListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsPlatformAdmin)
    serializer_class = NotificationSerializer
    queryset = Notification.objects.select_related("recipient", "actor", "post", "comment")

    def get_queryset(self):
        queryset = super().get_queryset()
        notification_type = self.request.query_params.get("type")
        read = self.request.query_params.get("read")
        if notification_type:
            if notification_type not in Notification.Type.values:
                raise ValidationError({"type": "Choose a supported notification type."})
            queryset = queryset.filter(type=notification_type)
        if read is not None:
            if read.lower() not in ("true", "false"):
                raise ValidationError({"read": "Use true or false."})
            queryset = queryset.filter(is_read=read.lower() == "true")
        return queryset


class AdminNotificationDeleteView(AdminEndpoint):
    def delete(self, request, pk):
        serializer = ModerationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        notification = get_object_or_404(Notification, pk=pk)
        remove_moderated_object(
            request,
            notification,
            target_type="notification",
            reason=serializer.validated_data["reason"].strip(),
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminRelationshipMonitoringView(AdminEndpoint):
    def get(self, request):
        relationships = Follow.objects.select_related("follower", "following")
        recent = relationships.order_by("-created_at")[:20]
        return Response(
            {
                "total_relationships": relationships.count(),
                "new_relationships_24h": relationships.filter(
                    created_at__gte=timezone.now() - timedelta(hours=24)
                ).count(),
                "recent": [
                    {
                        "follower": item.follower.username,
                        "following": item.following.username,
                        "created_at": item.created_at,
                    }
                    for item in recent
                ],
            }
        )


class AdminAuditListView(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsPlatformAdmin)
    serializer_class = AdminAuditLogSerializer

    def get(self, request):
        entries = AdminAuditLog.objects.select_related("admin")
        action = request.query_params.get("action")
        actor = request.query_params.get("actor")
        target = request.query_params.get("target")
        if action:
            entries = entries.filter(action=action)
        if actor:
            entries = entries.filter(admin__username__icontains=actor)
        if target:
            entries = entries.filter(target_type__icontains=target)
        page = self.paginate_queryset(entries)
        return self.get_paginated_response(self.get_serializer(page, many=True).data)


class AdminActivityView(AdminEndpoint):
    def get(self, request):
        start = request.query_params.get("from")
        end = request.query_params.get("to")
        start_date = parse_date(start) if start else None
        end_date = parse_date(end) if end else None
        if start and start_date is None:
            raise ValidationError({"from": "Use an ISO date."})
        if end and end_date is None:
            raise ValidationError({"to": "Use an ISO date."})
        if start_date and end_date and start_date > end_date:
            raise ValidationError({"to": "The end date must not precede the start date."})
        event_models = {
            "posts": Post,
            "comments": Comment,
            "likes": Like,
            "follows": Follow,
            "searches": SearchActivity,
            "notifications": Notification,
        }
        event_type = request.query_params.get("type")
        if event_type and event_type not in event_models:
            raise ValidationError({"type": "Choose a supported activity type."})
        selected = {event_type: event_models[event_type]} if event_type else event_models
        stats = {}
        for name, model in selected.items():
            queryset = model.objects.all()
            if start_date:
                queryset = queryset.filter(created_at__date__gte=start_date)
            if end_date:
                queryset = queryset.filter(created_at__date__lte=end_date)
            stats[name] = list(
                queryset.order_by()
                .values("created_at__date")
                .annotate(count=Count("pk"))
                .order_by("created_at__date")
            )
        return Response({"stats": stats})


class AdminSystemSettingListView(AdminEndpoint):
    def get(self, request):
        values = {setting.key: setting.value for setting in SystemSetting.objects.all()}
        from .services import PLATFORM_LIMITS
        from django.conf import settings

        for key, setting_name in PLATFORM_LIMITS.items():
            values.setdefault(key, getattr(settings, setting_name))
        return Response(values)

    def put(self, request):
        serializer = SystemSettingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        key = serializer.validated_data["key"]
        value = serializer.validated_data["value"]
        setting, created = SystemSetting.objects.update_or_create(
            key=key,
            defaults={"value": value, "updated_by": request.user},
        )
        record_admin_action(
            request,
            action="update_system_setting",
            target_type="system_setting",
            target_id=setting.pk,
            details={"key": key, "value": value, "created": created},
        )
        return Response(SystemSettingSerializer(setting).data)
