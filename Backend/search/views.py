from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.permissions import AllowAny

from accounts.models import User
from posts.models import Post
from posts.serializers import PostSerializer
from posts.services import posts_with_engagement
from profiles.services import profiles_with_relationship_counts

from .models import SearchActivity
from .filters import filter_users
from .serializers import (
    PostSearchSerializer,
    UserSearchResultSerializer,
    UserSearchSerializer,
)


class UserSearchView(generics.ListAPIView):
    serializer_class = UserSearchResultSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        serializer = UserSearchSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        term = serializer.validated_data["q"]
        SearchActivity.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            search_type=SearchActivity.SearchType.USERS,
        )
        return filter_users(
            profiles_with_relationship_counts(),
            term,
        ).order_by("username")


class PostSearchView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = (AllowAny,)

    def get_queryset(self):
        serializer = PostSearchSerializer(data=self.request.query_params)
        serializer.is_valid(raise_exception=True)
        filters = serializer.validated_data
        queryset = Post.objects.filter(author__is_active=True).select_related("author")
        term = filters.get("q", "").strip()
        if term:
            queryset = queryset.filter(content__icontains=term)
        if filters.get("author"):
            author = get_object_or_404(
                User.objects.filter(is_active=True),
                username=filters["author"],
            )
            queryset = queryset.filter(author=author)
        if filters.get("from_date"):
            queryset = queryset.filter(created_at__date__gte=filters["from_date"])
        if filters.get("to_date"):
            queryset = queryset.filter(created_at__date__lte=filters["to_date"])
        SearchActivity.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            search_type=SearchActivity.SearchType.POSTS,
        )
        return posts_with_engagement(
            queryset.prefetch_related("images").order_by("-created_at", "-pk"),
            self.request.user,
        )

    def get(self, request, *args, **kwargs):
        serializer = PostSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return super().get(request, *args, **kwargs)
