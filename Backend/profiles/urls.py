from django.urls import path

from .views import (
    MyProfileView,
    ProfileMediaDeleteView,
    ProfileMediaListCreateView,
    UserProfileView,
)

urlpatterns = [
    path("profiles/me/", MyProfileView.as_view(), name="my-profile"),
    path(
        "users/<str:username>/",
        UserProfileView.as_view(),
        name="user-profile",
    ),
    path(
        "users/<str:username>/media/",
        ProfileMediaListCreateView.as_view(),
        name="profile-media",
    ),
    path(
        "profile-media/<int:pk>/",
        ProfileMediaDeleteView.as_view(),
        name="profile-media-delete",
    ),
]
