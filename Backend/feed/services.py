from django.db.models import Q

from follows.models import Follow
from posts.models import Post
from posts.services import posts_with_engagement


def get_feed_posts(user):
    following_ids = Follow.objects.filter(
        follower=user,
        following__is_active=True,
    ).values("following_id")
    queryset = Post.objects.filter(author__is_active=True).filter(
        Q(author_id__in=following_ids) | Q(author=user)
    )
    return (
        posts_with_engagement(queryset, user)
        .prefetch_related("images")
        .order_by("-created_at", "-pk")
    )
