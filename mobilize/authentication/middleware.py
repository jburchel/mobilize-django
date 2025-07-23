import logging
from datetime import datetime, timedelta
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


class CustomAuthMiddleware(MiddlewareMixin):
    """
    Custom middleware to handle authentication with manual session variables.
    This bridges our raw SQL user creation with Django's authentication system.
    """

    def process_request(self, request):
        # First check if user is already authenticated via Django's standard auth system
        # (This handles OAuth callback logins)
        if hasattr(request, "user") and request.user.is_authenticated:
            # User is already authenticated via Django's auth system, don't override
            return None

        # Check if user is authenticated via our manual session
        if request.session.get("authenticated") and request.session.get("user_id"):
            # Create a minimal user object that Django's auth system will accept
            class AuthenticatedUser:
                def __init__(self, user_id, email):
                    self.id = int(user_id)  # Ensure it's an integer for Django ORM
                    self.pk = int(user_id)  # Django compatibility
                    self.email = email
                    self.username = email
                    self.is_authenticated = True
                    self.is_active = True
                    self.is_anonymous = False
                    self.is_staff = False
                    self.is_superuser = False
                    # Add missing attributes for CRM decorators
                    # Query the database for the actual user role
                    try:
                        from mobilize.authentication.models import User
                        db_user = User.objects.get(id=user_id)
                        self.role = db_user.role
                        self.first_name = db_user.first_name
                        self.last_name = db_user.last_name
                        self.preferences = db_user.preferences or {}
                        self.person = db_user.person
                        # Set staff/superuser based on role
                        if self.role == "super_admin":
                            self.is_staff = True
                            self.is_superuser = True
                        elif self.role == "office_admin":
                            self.is_staff = True
                    except User.DoesNotExist:
                        # Fallback to standard_user if user not found in database
                        self.role = "standard_user"
                        self.first_name = ""
                        self.last_name = ""
                        self.preferences = {}
                        self.person = None

                def get_username(self):
                    return self.email

                def __str__(self):
                    return self.email

                def has_perm(self, perm, obj=None):
                    return True  # Temporary - allow all permissions

                def has_perms(self, perm_list, obj=None):
                    return True  # Temporary - allow all permissions

                def has_module_perms(self, package_name):
                    return True  # Temporary - allow all permissions

                def has_office_permission(self, office_id, required_role=None):
                    return True  # Temporary - allow all office access

                def get_or_create_person(self):
                    return None  # Temporary - no person record

            # Set the user on the request
            request.user = AuthenticatedUser(
                request.session["user_id"], request.session["user_email"]
            )
        else:
            # User is not authenticated
            request.user = AnonymousUser()


class UserActivityTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track user activity and trigger Gmail sync when users
    become active after periods of inactivity.
    """

    # Consider a user inactive after 2 hours of no activity
    INACTIVITY_THRESHOLD = timedelta(hours=2)

    def process_request(self, request):
        """
        Track user activity and trigger email sync if user was inactive.
        """
        # Only track authenticated users
        if not hasattr(request, "user") or not request.user.is_authenticated:
            return None

        # Skip AJAX requests and static file requests to avoid excessive tracking
        if (
            request.headers.get("X-Requested-With") == "XMLHttpRequest"
            or request.path.startswith("/static/")
            or request.path.startswith("/media/")
        ):
            return None

        try:
            user = request.user
            now = timezone.now()

            # Cache keys for tracking activity
            last_activity_key = f"user_last_activity_{user.id}"
            inactive_sync_key = f"user_inactive_sync_{user.id}"

            # Get user's last activity time
            last_activity_str = cache.get(last_activity_key)
            last_activity = None

            if last_activity_str:
                try:
                    last_activity = datetime.fromisoformat(
                        last_activity_str.replace("Z", "+00:00")
                    )
                    if last_activity.tzinfo is None:
                        last_activity = timezone.make_aware(last_activity)
                except (ValueError, AttributeError):
                    # Invalid datetime format, treat as no previous activity
                    last_activity = None

            # Check if user was inactive and is now active
            was_inactive = False
            if last_activity:
                time_since_activity = now - last_activity
                was_inactive = time_since_activity > self.INACTIVITY_THRESHOLD
            else:
                # No previous activity recorded, consider as returning from inactivity
                was_inactive = True

            # Update last activity time
            cache.set(
                last_activity_key, now.isoformat(), timeout=86400 * 7
            )  # Keep for 7 days

            # If user was inactive and we haven't already triggered sync recently
            if was_inactive:
                recent_inactive_sync = cache.get(inactive_sync_key)
                if not recent_inactive_sync:
                    # Trigger Gmail sync after inactivity
                    from mobilize.communications.signals import (
                        trigger_gmail_sync_after_inactivity,
                    )

                    trigger_gmail_sync_after_inactivity(user)

                    # Mark that we've triggered sync for this inactive period
                    cache.set(
                        inactive_sync_key, True, timeout=7200
                    )  # Don't sync again for 2 hours

                    logger.info(
                        f"User {user.username} detected as active after inactivity"
                    )

        except Exception as e:
            logger.error(f"Error in UserActivityTrackingMiddleware: {str(e)}")

        return None
