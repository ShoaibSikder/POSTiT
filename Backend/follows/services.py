from .models import Follow
from notifications.models import Notification
from notifications.services import notify


def follow_user(follower, following):
    relationship, created = Follow.objects.get_or_create(
        follower=follower,
        following=following,
    )
    if created:
        notify(following, follower, Notification.Type.FOLLOW)
    return relationship, created


def unfollow_user(follower, following):
    Follow.objects.filter(follower=follower, following=following).delete()


def active_follower_count(user):
    return user.follower_relationships.filter(follower__is_active=True).count()
