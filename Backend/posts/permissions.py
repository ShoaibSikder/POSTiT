from common.permissions import IsOwnerOrReadOnly


class IsPostOwnerOrReadOnly(IsOwnerOrReadOnly):
    message = "You can only change your own posts."
