from django.urls import path

from .views import NotificationListView, NotificationReadAllView, NotificationReadView

urlpatterns = [
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("notifications/read-all/", NotificationReadAllView.as_view(), name="notifications-read-all"),
    path("notifications/<int:pk>/read/", NotificationReadView.as_view(), name="notification-read"),
]

