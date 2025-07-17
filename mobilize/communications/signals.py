import logging
from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model

from .models import Communication
from .tasks import sync_gmail_emails
from mobilize.contacts.models import Person, Contact

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
            Communication.objects.filter(pk=instance.pk).update(
                updated_at=timezone.now().date()
            )


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
                    sync_gmail_emails.delay(
                        user.id, days_back=3
                    )  # Sync more days on login

                    # Mark as recently synced (prevent duplicate syncs for 30 minutes)
                    cache.set(cache_key, True, timeout=1800)

                    logger.info(
                        f"Triggered Gmail sync for user {user.username} on login"
                    )
                else:
                    logger.debug(
                        f"Skipped Gmail sync for user {user.username} - recently synced"
                    )

        except GoogleToken.DoesNotExist:
            logger.debug(f"User {user.username} has no Gmail authentication")

    except Exception as e:
        logger.error(
            f"Error triggering Gmail sync on login for user {user.username}: {str(e)}"
        )


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
            cache.set(
                cache_key, timezone.now().isoformat(), timeout=86400 * 7
            )  # Keep for 7 days

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

                logger.info(
                    f"Triggered Gmail sync for user {user.username} after inactivity"
                )

        except GoogleToken.DoesNotExist:
            logger.debug(f"User {user.username} has no Gmail authentication")

    except Exception as e:
        logger.error(
            f"Error triggering Gmail sync after inactivity for user {user.username}: {str(e)}"
        )


@receiver(post_save, sender=Person)
def trigger_gmail_sync_for_new_person(sender, instance, created, **kwargs):
    """
    Signal handler to trigger Gmail sync when a new person is created.

    This will sync emails to/from the new person's email address to ensure
    all historical communications are captured in the CRM.

    Args:
        sender: The Person model class
        instance: The Person instance that was saved
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    if created and instance.contact and instance.contact.email:
        try:
            # Get the user who created this person (or their assigned user)
            user = instance.contact.user
            if not user:
                logger.debug(
                    f"New person {instance.contact.first_name} {instance.contact.last_name} has no assigned user, skipping Gmail sync"
                )
                return

            # Check if user has Gmail authentication
            from mobilize.authentication.models import GoogleToken

            try:
                google_token = GoogleToken.objects.get(user=user)
                if google_token.access_token:
                    # Queue Gmail sync for this user focusing on the new contact's email
                    # Use more days back to capture historical emails with this person
                    sync_gmail_emails.delay(user.id, days_back=30)

                    logger.info(
                        f"Triggered Gmail sync for user {user.username} due to new person: "
                        f"{instance.contact.first_name} {instance.contact.last_name} ({instance.contact.email})"
                    )
                else:
                    logger.debug(f"User {user.username} has no Gmail access token")

            except GoogleToken.DoesNotExist:
                logger.debug(f"User {user.username} has no Gmail authentication")

        except Exception as e:
            logger.error(
                f"Error triggering Gmail sync for new person "
                f"{instance.contact.first_name} {instance.contact.last_name}: {str(e)}"
            )


@receiver(post_save, sender=Contact)
def trigger_gmail_sync_for_new_contact(sender, instance, created, **kwargs):
    """
    Signal handler to trigger Gmail sync when a new contact with email is created.

    This handles cases where Contact records are created directly (e.g., during import)
    before Person records are created.

    Args:
        sender: The Contact model class
        instance: The Contact instance that was saved
        created: Boolean indicating if this is a new record
        **kwargs: Additional keyword arguments
    """
    if created and instance.email and instance.type == "person":
        try:
            # Get the user who created this contact
            user = instance.user
            if not user:
                logger.debug(
                    f"New contact {instance.first_name} {instance.last_name} has no assigned user, skipping Gmail sync"
                )
                return

            # Check if user has Gmail authentication
            from mobilize.authentication.models import GoogleToken

            try:
                google_token = GoogleToken.objects.get(user=user)
                if google_token.access_token:
                    # Queue Gmail sync for this user focusing on the new contact's email
                    # Use more days back to capture historical emails with this contact
                    sync_gmail_emails.delay(user.id, days_back=30)

                    logger.info(
                        f"Triggered Gmail sync for user {user.username} due to new contact: "
                        f"{instance.first_name} {instance.last_name} ({instance.email})"
                    )
                else:
                    logger.debug(f"User {user.username} has no Gmail access token")

            except GoogleToken.DoesNotExist:
                logger.debug(f"User {user.username} has no Gmail authentication")

        except Exception as e:
            logger.error(
                f"Error triggering Gmail sync for new contact "
                f"{instance.first_name} {instance.last_name}: {str(e)}"
            )
