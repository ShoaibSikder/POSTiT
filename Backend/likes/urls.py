from django.urls import path

from .views import PostLikeView

urlpatterns = [
    path(
        "posts/<int:post_id>/like/",
        PostLikeView.as_view(),
        name="post-like",
    ),
]
