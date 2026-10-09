from .models import Like
from notifications.models import Notification
from notifications.services import notify


def like_post(post, user):
    like, created = Like.objects.get_or_create(post=post, user=user)
    if created:
        notify(post.author, user, Notification.Type.LIKE, post=post)
    return like, created


def unlike_post(post, user):
    Like.objects.filter(post=post, user=user).delete()
