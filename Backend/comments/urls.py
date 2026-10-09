from django.urls import path

from .views import CommentDetailView, PostCommentListCreateView

urlpatterns = [
    path(
        "posts/<int:post_id>/comments/",
        PostCommentListCreateView.as_view(),
        name="post-comments",
    ),
    path(
        "comments/<int:pk>/",
        CommentDetailView.as_view(),
        name="comment-detail",
    ),
]
