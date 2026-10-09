from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User

from .models import Follow
from .serializers import UserSummarySerializer
from .services import active_follower_count, follow_user, unfollow_user


class FollowView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, username):
        target = self._get_target(username)
        if request.user.pk == target.pk:
            return Response(
                {"detail": "You cannot follow yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        follow_user(request.user, target)
        return Response(
            {
                "following": True,
                "follower_count": active_follower_count(target),
            },
            status=status.HTTP_200_OK,
        )

    def delete(self, request, username):
        target = self._get_target(username)
        unfollow_user(request.user, target)
        return Response(
            {
                "following": False,
                "follower_count": active_follower_count(target),
            },
            status=status.HTTP_200_OK,
        )

    @staticmethod
    def _get_target(username):
        return get_object_or_404(User.objects.filter(is_active=True), username=username)


class UserRelationshipListView(generics.ListAPIView):
    serializer_class = UserSummarySerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_queryset(self):
        target = get_object_or_404(
            User.objects.filter(is_active=True),
            username=self.kwargs["username"],
        )
        relation = self.kwargs["relation"]
        if relation == "followers":
            relationships = Follow.objects.filter(
                following=target,
                follower__is_active=True,
            )
            user_field = "follower"
        elif relation == "following":
            relationships = Follow.objects.filter(
                follower=target,
                following__is_active=True,
            )
            user_field = "following"
        else:
            raise Http404
        user_ids = relationships.values_list(f"{user_field}_id", flat=True)
        return User.objects.filter(pk__in=user_ids).order_by("username")
