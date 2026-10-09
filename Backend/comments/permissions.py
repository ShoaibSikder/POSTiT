from common.permissions import IsOwnerOrReadOnly


class IsCommentAuthorOrReadOnly(IsOwnerOrReadOnly):
    message = "You can only change your own comments."
