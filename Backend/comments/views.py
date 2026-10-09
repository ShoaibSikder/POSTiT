from django.shortcuts import get_object_or_404
from django.db import transaction
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from posts.models import Post
from notifications.models import Notification
from notifications.services import notify

from .models import Comment
from .permissions import IsCommentAuthorOrReadOnly
from .serializers import CommentSerializer
from .services import get_active_post_comments


class PostCommentListCreateView(generics.ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_post(self):
        if not hasattr(self, "_post"):
            self._post = get_object_or_404(
                Post.objects.filter(author__is_active=True),
                pk=self.kwargs["post_id"],
            )
        return self._post

    def get_queryset(self):
        return get_active_post_comments(self.get_post())

    def perform_create(self, serializer):
        post = self.get_post()
        with transaction.atomic():
            comment = serializer.save(post=post, author=self.request.user)
            notify(
                post.author,
                self.request.user,
                Notification.Type.COMMENT,
                post=post,
                comment=comment,
            )


class CommentDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = (
        IsAuthenticatedOrReadOnly,
        IsCommentAuthorOrReadOnly,
    )
    http_method_names = ("get", "patch", "delete", "head", "options")

    def get_queryset(self):
        return Comment.objects.filter(
            author__is_active=True,
            post__author__is_active=True,
        ).select_related("author", "post")
