from django.db import models
from django.conf import settings
from django.utils import timezone


class ActivityLog(models.Model):
    """
    Model for tracking user activities within the system.

    This model records various actions performed by users across different
    parts of the application, providing an audit trail of system usage.
    """

    # Activity Information
    ACTION_CHOICES = (
        ("create", "Create"),
        ("update", "Update"),
        ("delete", "Delete"),
        ("view", "View"),
        ("login", "Login"),
        ("logout", "Logout"),
        ("export", "Export"),
        ("import", "Import"),
        ("sync", "Synchronization"),
        ("email", "Email"),
        ("other", "Other"),
    )

    action_type = models.CharField(
        max_length=50, choices=ACTION_CHOICES, default="other"
    )
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True, null=True)

    # Entity being acted upon
    entity_type = models.CharField(max_length=50, blank=True, null=True)
    entity_id = models.IntegerField(blank=True, null=True)

    # Additional context data (stored as JSON)
    details = models.JSONField(blank=True, null=True)

    # User who performed the action
    user = models.ForeignKey(  # Corresponds to User model in mobilize-prompt-django.md
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="activity_logs",
    )

    # Office context
    office = models.ForeignKey(
        "admin_panel.Office",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="activity_logs",
    )

    # Timestamps
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        db_table = "activity_logs"  # As per mobilize-prompt-django.md
        verbose_name = "Activity Log"
        verbose_name_plural = "Activity Logs"
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["action_type"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["user"]),
            models.Index(
                fields=["entity_type", "entity_id"]
            ),  # As per mobilize-prompt-django.md
        ]

    def __str__(self):
        if self.user:
            user_str = (
                self.user.get_full_name() or self.user.email
            )  # Use email as fallback
        else:
            user_str = "System"

        return f"{user_str} - {self.get_action_type_display()} on {self.entity_type or 'N/A'}({self.entity_id or 'N/A'}) - {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def log_activity(
        cls,
        user,
        action_type,
        entity_type=None,
        entity_id=None,
        content_object=None,
        details=None,
        request=None,
        office=None,
        description_text=None,
    ):
        """
        Helper method to easily log an activity.

        Args:
            user: The user who performed the action
            action: The type of action (must be one of ACTION_CHOICES)
            description: A description of the activity
            entity_type: String representing the type of the entity (e.g., 'person', 'task')
            entity_id: Integer ID of the entity
            content_object: The related Django model instance (optional, can derive entity_type/id)
            details: Any additional context data as dict (optional)
            request: The HTTP request object (optional, to extract IP and user agent)
            office: The office context (optional)
            description_text: A simple text message to include in details (optional)

        Returns:
            The created ActivityLog instance
        """
        current_details = details.copy() if isinstance(details, dict) else {}

        if content_object and entity_type is None and entity_id is None:
            entity_type = content_object._meta.model_name
            entity_id = content_object.pk

        if description_text:
            current_details["message"] = description_text

        final_details = current_details if current_details else None

        activity = cls(
            user=user,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            details=final_details,
            office=office,
        )

        # Extract IP and user agent from request if provided
        if request:
            activity.ip_address = request.META.get("REMOTE_ADDR")
            activity.user_agent = request.META.get("HTTP_USER_AGENT")
        activity.save()
        return activity


class DashboardPreference(models.Model):
    """
    Model to store user dashboard preferences.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="dashboard_preferences",
    )
    widget_config = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "dashboard_preferences"

    def __str__(self):
        return f"Dashboard preferences for {self.user.username}"

    def get_widget_config(self):
        """
        Get the user's widget configuration, falling back to defaults.

        Returns:
            List of widget configurations
        """
        from mobilize.core.dashboard_widgets import DEFAULT_WIDGETS

        if self.widget_config:
            return self.widget_config.get("widgets", DEFAULT_WIDGETS)
        return DEFAULT_WIDGETS

    def set_widget_config(self, widgets):
        """
        Set the user's widget configuration.

        Args:
            widgets: List of widget configurations
        """
        self.widget_config = {"widgets": widgets}
        self.save()

    def get_enabled_widgets(self):
        """
        Get only enabled widgets, sorted by order.

        Returns:
            List of enabled widget configurations
        """
        widgets = self.get_widget_config()
        enabled_widgets = [w for w in widgets if w.get("enabled", True)]
        return sorted(enabled_widgets, key=lambda x: x.get("order", 999))

    def reset_to_defaults(self):
        """
        Reset widget configuration to defaults.
        """
        from mobilize.core.dashboard_widgets import DEFAULT_WIDGETS

        self.widget_config = {"widgets": DEFAULT_WIDGETS}
        self.save()
