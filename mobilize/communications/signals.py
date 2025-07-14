import logging
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from .models import Communication
from .tasks import sync_gmail_emails

logger = logging.getLogger(__name__)
User = get_user_model()


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


@receiver(user_logged_in)
def trigger_gmail_sync_on_login(sender, request, user, **kwargs):
    """
    Trigger Gmail sync when user logs in.
    
    This ensures the user gets their latest emails immediately upon login,
    especially useful for users who haven't been active recently.
    """
    try:
        # Check if user has Gmail authentication
        from mobilize.authentication.models import GoogleToken
        try:
            google_token = GoogleToken.objects.get(user=user)
            if google_token.access_token:
                # Check if we've synced recently to avoid duplicate syncs
                cache_key = f"gmail_sync_recent_{user.id}"
                recent_sync = cache.get(cache_key)
                
                if not recent_sync:
                    # Queue Gmail sync for this user
                    sync_gmail_emails.delay(user.id, days_back=3)  # Sync more days on login
                    
                    # Mark as recently synced (prevent duplicate syncs for 30 minutes)
                    cache.set(cache_key, True, timeout=1800)
                    
                    logger.info(f"Triggered Gmail sync for user {user.username} on login")
                else:
                    logger.debug(f"Skipped Gmail sync for user {user.username} - recently synced")
                    
        except GoogleToken.DoesNotExist:
            logger.debug(f"User {user.username} has no Gmail authentication")
            
    except Exception as e:
        logger.error(f"Error triggering Gmail sync on login for user {user.username}: {str(e)}")


@receiver(user_logged_out)
def mark_user_inactive_on_logout(sender, request, user, **kwargs):
    """
    Mark user as inactive when they log out.
    
    This helps track user activity patterns and trigger sync when they return.
    """
    try:
        if user and user.is_authenticated:
            # Store logout timestamp for activity tracking
            cache_key = f"user_last_logout_{user.id}"
            cache.set(cache_key, timezone.now().isoformat(), timeout=86400 * 7)  # Keep for 7 days
            
            logger.debug(f"Marked user {user.username} as inactive on logout")
            
    except Exception as e:
        logger.error(f"Error marking user inactive on logout: {str(e)}")


def trigger_gmail_sync_after_inactivity(user):
    """
    Trigger Gmail sync for a user who has been inactive and is now active.
    
    This function is called by the activity tracking middleware when it detects
    that a user has been inactive for a significant period.
    
    Args:
        user: The User instance who has become active again
    """
    try:
        # Check if user has Gmail authentication
        from mobilize.authentication.models import GoogleToken
        try:
            google_token = GoogleToken.objects.get(user=user)
            if google_token.access_token:
                # Queue Gmail sync for this user with more days back since they've been inactive
                sync_gmail_emails.delay(user.id, days_back=7)
                
                logger.info(f"Triggered Gmail sync for user {user.username} after inactivity")
                
        except GoogleToken.DoesNotExist:
            logger.debug(f"User {user.username} has no Gmail authentication")
            
    except Exception as e:
        logger.error(f"Error triggering Gmail sync after inactivity for user {user.username}: {str(e)}")
