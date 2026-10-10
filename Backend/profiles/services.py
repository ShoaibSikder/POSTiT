from django.db.models import Count, Q

from accounts.models import User


def profiles_with_relationship_counts():
    return (
        User.objects.filter(is_active=True)
        .select_related("profile")
        .annotate(
            follower_count=Count(
                "follower_relationships",
                filter=Q(follower_relationships__follower__is_active=True),
                distinct=True,
            ),
            following_count=Count(
                "following_relationships",
                filter=Q(following_relationships__following__is_active=True),
                distinct=True,
            ),
            post_count=Count("posts", distinct=True),
        )
    )
