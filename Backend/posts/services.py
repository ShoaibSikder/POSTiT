from django.db.models import BooleanField, Count, Exists, OuterRef, Q, Value

from likes.models import Like


def posts_with_engagement(queryset, user):
    liked_by_user = Like.objects.filter(post_id=OuterRef("pk"))
    if user.is_authenticated:
        liked_by_user = liked_by_user.filter(user_id=user.pk)
    else:
        liked_by_user = Like.objects.none()
    return queryset.annotate(
        likes_count=Count(
            "likes",
            filter=Q(likes__user__is_active=True),
            distinct=True,
        ),
        comments_count=Count(
            "comments",
            filter=Q(comments__author__is_active=True),
            distinct=True,
        ),
        liked_by_user=Exists(liked_by_user)
        if user.is_authenticated
        else Value(False, output_field=BooleanField()),
    )
