from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsOwnerOrReadOnly(BasePermission):
    message = "You can only change content that you own."

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        owner = getattr(obj, "author", None) or getattr(obj, "user", None)
        return owner is not None and owner.pk == request.user.pk

