from django.db import transaction
from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from accounts.models import User
from profiles.models import Profile, ProfileMedia


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(user=instance)


def schedule_file_delete(field_file):
    if field_file and field_file.name:
        storage = field_file.storage
        name = field_file.name
        transaction.on_commit(lambda: storage.delete(name))


@receiver(pre_save, sender=Profile)
@receiver(pre_save, sender=ProfileMedia)
def delete_replaced_profile_image(sender, instance, **kwargs):
    if not instance.pk:
        return

    previous = sender.objects.filter(pk=instance.pk).first()
    if previous is None:
        return

    for field_name in ("avatar", "cover_image", "image"):
        if hasattr(instance, field_name):
            old_file = getattr(previous, field_name)
            new_file = getattr(instance, field_name)
            if old_file and old_file.name != new_file.name:
                schedule_file_delete(old_file)


@receiver(post_delete, sender=Profile)
@receiver(post_delete, sender=ProfileMedia)
def delete_profile_images(sender, instance, **kwargs):
    for field_name in ("avatar", "cover_image", "image"):
        if hasattr(instance, field_name):
            schedule_file_delete(getattr(instance, field_name))
