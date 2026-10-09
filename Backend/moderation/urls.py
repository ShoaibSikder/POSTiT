from django.urls import path

from .views import (
    AdminAuditListView,
    AdminCommentDeleteView,
    AdminCommentListView,
    AdminDashboardView,
    AdminMediaDeleteView,
    AdminMediaListView,
    AdminNotificationDeleteView,
    AdminNotificationListView,
    AdminPostDeleteView,
    AdminPostListView,
    AdminRelationshipMonitoringView,
    AdminSystemSettingListView,
    AdminUserListView,
    AdminUserActionView,
    AdminActivityView,
)

urlpatterns = [
    path("admin/dashboard/", AdminDashboardView.as_view(), name="admin-dashboard"),
    path("admin/users/", AdminUserListView.as_view(), name="admin-users"),
    path("admin/users/<int:pk>/<str:action>/", AdminUserActionView.as_view(), name="admin-user-action"),
    path("admin/posts/", AdminPostListView.as_view(), name="admin-posts"),
    path("admin/posts/<int:pk>/", AdminPostDeleteView.as_view(), name="admin-post-delete"),
    path("admin/comments/", AdminCommentListView.as_view(), name="admin-comments"),
    path("admin/comments/<int:pk>/", AdminCommentDeleteView.as_view(), name="admin-comment-delete"),
    path("admin/media/<str:media_type>/<int:pk>/", AdminMediaDeleteView.as_view(), name="admin-media-delete"),
    path("admin/media/<str:media_type>/", AdminMediaListView.as_view(), name="admin-media-list"),
    path("admin/notifications/", AdminNotificationListView.as_view(), name="admin-notifications"),
    path("admin/notifications/<int:pk>/", AdminNotificationDeleteView.as_view(), name="admin-notification-delete"),
    path("admin/relationships/", AdminRelationshipMonitoringView.as_view(), name="admin-relationships"),
    path("admin/audit/", AdminAuditListView.as_view(), name="admin-audit"),
    path("admin/activity/", AdminActivityView.as_view(), name="admin-activity"),
    path("admin/settings/", AdminSystemSettingListView.as_view(), name="admin-settings"),
]
