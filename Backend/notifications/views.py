from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from common.responses import success_response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationListView(generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return Notification.objects.filter(recipient=self.request.user).select_related(
            "actor", "post", "comment"
        )

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["unread"] = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).count()
        return response


class NotificationReadView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, pk):
        notification = get_object_or_404(
            Notification.objects.filter(recipient=request.user),
            pk=pk,
        )
        if not notification.is_read:
            notification.is_read = True
            notification.save(update_fields=("is_read",))
        return success_response(
            NotificationSerializer(notification).data,
            status=status.HTTP_200_OK,
        )


class NotificationReadAllView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user,
            is_read=False,
        ).update(is_read=True)
        return success_response({"updated": updated}, status=status.HTTP_200_OK)
