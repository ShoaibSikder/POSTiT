from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsProfileOwnerOrReadOnly(BasePermission):
    message = "You can only change your own profile."

    def has_object_permission(self, request, view, profile):
        return (
            request.method in SAFE_METHODS
            or request.user.is_authenticated
            and profile.user_id == request.user.pk
        )

