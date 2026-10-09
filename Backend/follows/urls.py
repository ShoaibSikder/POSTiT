from django.urls import path

from .views import FollowView, UserRelationshipListView

urlpatterns = [
    path(
        "users/<str:username>/follow/",
        FollowView.as_view(),
        name="user-follow",
    ),
    path(
        "users/<str:username>/<str:relation>/",
        UserRelationshipListView.as_view(),
        name="user-relationships",
    ),
]
