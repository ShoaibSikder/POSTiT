from django.shortcuts import get_object_or_404
from rest_framework import generics
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticatedOrReadOnly

from .models import ProfileMedia
from .permissions import IsProfileOwnerOrReadOnly
from .serializers import ProfileMediaCreateSerializer, ProfileMediaSerializer, ProfileSerializer
from .services import profiles_with_relationship_counts


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    lookup_field = "username"
    lookup_url_kwarg = "username"

    def get_queryset(self):
        return profiles_with_relationship_counts()

    def get_object(self):
        user = get_object_or_404(
            self.get_queryset(),
            username=self.kwargs["username"],
        )
        profile = user.profile
        if not IsProfileOwnerOrReadOnly().has_object_permission(
            self.request,
            self,
            profile,
        ):
            raise PermissionDenied("You can only edit your own profile.")
        return profile


class MyProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get_object(self):
        if not self.request.user.is_authenticated:
            raise PermissionDenied("Authentication is required.")
        return self.request.user.profile


class ProfileMediaListCreateView(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ProfileMediaSerializer

    def get_profile(self):
        user = get_object_or_404(
            profiles_with_relationship_counts(),
            username=self.kwargs["username"],
        )
        if (
            self.request.method == "POST"
            and user.pk != self.request.user.pk
        ):
            raise PermissionDenied("You can only add media to your own profile.")
        return user.profile

    def get_queryset(self):
        return ProfileMedia.objects.filter(profile=self.get_profile())

    def get_serializer_class(self):
        if self.request.method == "POST":
            return ProfileMediaCreateSerializer
        return ProfileMediaSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        if self.request.method == "POST":
            context["profile"] = self.get_profile()
        return context

    def perform_create(self, serializer):
        profile = self.get_profile()
        if profile.user_id != self.request.user.pk:
            raise PermissionDenied("You can only add media to your own profile.")
        serializer.save()


class ProfileMediaDeleteView(generics.DestroyAPIView):
    permission_classes = (IsAuthenticatedOrReadOnly,)
    serializer_class = ProfileMediaSerializer

    def get_queryset(self):
        if not self.request.user.is_authenticated:
            return ProfileMedia.objects.none()
        return ProfileMedia.objects.filter(profile__user=self.request.user)
