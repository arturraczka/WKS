from django.db.models.signals import post_init, post_save
from django.dispatch import receiver

from apps.user.models import UserProfile
from django.contrib.auth import get_user_model

ModelUser = get_user_model()


@receiver(post_save, sender=ModelUser)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        profile = UserProfile(user=instance)
        profile.save()
