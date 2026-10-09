from django.urls import path

from .views import PostDetailView, PostListCreateView, UserPostListView

urlpatterns = [
    path("posts/", PostListCreateView.as_view(), name="post-list"),
    path("posts/<int:pk>/", PostDetailView.as_view(), name="post-detail"),
    path(
        "users/<str:username>/posts/",
        UserPostListView.as_view(),
        name="user-posts",
    ),
]
