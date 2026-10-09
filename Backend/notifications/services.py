from .models import Notification


def notify(recipient, actor, notification_type, *, post=None, comment=None):
    if recipient.pk == actor.pk or not recipient.is_active:
        return None
    return Notification.objects.create(
        recipient=recipient,
        actor=actor,
        type=notification_type,
        post=post,
        comment=comment,
    )

