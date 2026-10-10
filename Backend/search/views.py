from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated

from accounts.models import User
from profiles.services import profiles_with_relationship_counts
from posts.models import Post
from posts.serializers import PostSerializer
from posts.services import posts_with_engagement

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
        if not term and not self.request.user.is_authenticated:
            raise NotAuthenticated("Sign in to browse all people.")
        SearchActivity.objects.create(
            user=self.request.user if self.request.user.is_authenticated else None,
            search_type=SearchActivity.SearchType.USERS,
        )
        queryset = profiles_with_relationship_counts()
        if self.request.user.is_authenticated:
            queryset = queryset.exclude(pk=self.request.user.pk)
        if term:
            queryset = filter_users(queryset, term)
        return queryset.order_by("username")


class UserSuggestionsView(generics.ListAPIView):
    serializer_class = UserSearchResultSerializer
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        user = self.request.user
        followed_users = user.following_relationships.values_list(
            "following_id", flat=True
        )
        return (
            profiles_with_relationship_counts()
            .exclude(pk=user.pk)
            .exclude(pk__in=followed_users)
            .order_by("-follower_count", "username")
        )


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
