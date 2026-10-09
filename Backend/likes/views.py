from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from posts.models import Post

from .serializers import LikeStatusSerializer
from .services import like_post, unlike_post


class PostLikeView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, post_id):
        post = get_object_or_404(
            Post.objects.filter(author__is_active=True),
            pk=post_id,
        )
        like_post(post, request.user)
        return self._response(post, liked=True)

    def delete(self, request, post_id):
        post = get_object_or_404(
            Post.objects.filter(author__is_active=True),
            pk=post_id,
        )
        unlike_post(post, request.user)
        return self._response(post, liked=False)

    @staticmethod
    def _response(post, liked):
        data = LikeStatusSerializer(
            {
                "liked": liked,
                "likes_count": post.likes.filter(user__is_active=True).count(),
            }
        ).data
        return Response(data, status=status.HTTP_200_OK)
