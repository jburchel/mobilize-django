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
        # If marked as read but read_at is not set
        if instance.is_read and not instance.read_at:
            instance.read_at = timezone.now()
            # Use update to avoid triggering this signal again
            Communication.objects.filter(pk=instance.pk).update(read_at=instance.read_at)
            
        # If marked as delivered but delivered_at is not set
        if instance.delivered and not instance.delivered_at:
            instance.delivered_at = timezone.now()
            # Use update to avoid triggering this signal again
            Communication.objects.filter(pk=instance.pk).update(delivered_at=instance.delivered_at)
