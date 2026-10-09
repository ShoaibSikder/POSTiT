from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from accounts.models import User

from .models import Post, PostImage
from .filters import PostFilterBackend
from .pagination import PostPagination
from .permissions import IsPostOwnerOrReadOnly
from .serializers import PostSerializer
from .services import posts_with_engagement


class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (PostFilterBackend,)
    pagination_class = PostPagination

    def get_queryset(self):
        return posts_with_engagement(
            Post.objects.filter(author__is_active=True)
            .select_related("author")
            .prefetch_related(
                Prefetch(
                    "images",
                    queryset=PostImage.objects.order_by("created_at", "pk"),
                )
            ),
            self.request.user,
        )


class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = PostSerializer
    permission_classes = (IsAuthenticatedOrReadOnly, IsPostOwnerOrReadOnly)

    def get_queryset(self):
        return posts_with_engagement(
            Post.objects.filter(author__is_active=True).select_related("author"),
            self.request.user,
        ).prefetch_related("images")


class UserPostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = PostPagination

    def get_queryset(self):
        user = get_object_or_404(
            User.objects.filter(is_active=True),
            username=self.kwargs["username"],
        )
        return posts_with_engagement(
            Post.objects.filter(author=user)
            .select_related("author")
            .prefetch_related("images"),
            self.request.user,
        )
