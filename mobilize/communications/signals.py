from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Communication


@receiver(post_save, sender=Communication)
def update_communication_timestamps(sender, instance, created, **kwargs):
    """
    Signal handler to update timestamp fields on Communication objects
    based on their status changes.
    """
    # Only process if this is an update (not a new creation)
    if not created:
        # Update the updated_at field when communication is modified
        if not instance.updated_at:
            Communication.objects.filter(pk=instance.pk).update(updated_at=timezone.now().date())
