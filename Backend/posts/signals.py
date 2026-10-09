from django.db import transaction
from django.db.models.signals import post_delete
from django.dispatch import receiver

from posts.models import PostImage


@receiver(post_delete, sender=PostImage)
def delete_post_image_file(sender, instance, **kwargs):
    if instance.image and instance.image.name:
        storage = instance.image.storage
        name = instance.image.name
        transaction.on_commit(lambda: storage.delete(name))
