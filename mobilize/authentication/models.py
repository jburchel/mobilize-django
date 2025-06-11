from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    
    Adds role-based permissions and user preferences.
    """
    role = models.CharField(
        max_length=20, 
        default='standard_user',
        choices=(
            ('super_admin', 'Super Admin'),
            ('office_admin', 'Office Admin'),
            ('standard_user', 'Standard User'),
            ('limited_user', 'Limited User'),
        )
    )
    preferences = models.JSONField(blank=True, null=True)
    email_signature = models.TextField(blank=True, null=True)
    notification_settings = models.JSONField(blank=True, null=True)
    theme_preferences = models.JSONField(blank=True, null=True)
    google_refresh_token = models.TextField(blank=True, null=True)
    profile_picture_url = models.URLField(max_length=255, blank=True, null=True)
    
    class Meta:
        db_table = 'users'
        indexes = [
            models.Index(fields=['email']),
        ]
    
    def has_office_permission(self, office_id, required_role=None):
        """
        Check if user has permission for a specific office.
        
        Args:
            office_id: The ID of the office to check permissions for
            required_role: Optional role requirement (e.g., 'office_admin')
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # Super admins have access to everything
        if self.role == 'super_admin':
            return True
            
        # Check if user is assigned to this office
        user_office = self.useroffice_set.filter(office_id=office_id).first()
        
        if not user_office:
            return False
            
        # If a specific role is required, check for it
        if required_role and user_office.role != required_role:
            return False
            
        return True
    
    def has_perm(self, perm, obj=None):
        """
        Override default permission check to implement role-based permissions.
        
        Args:
            perm: The permission string to check
            obj: Optional object to check permissions against
            
        Returns:
            bool: True if user has permission, False otherwise
        """
        # Super admins have all permissions
        if self.role == 'super_admin':
            return True
            
        # Office admins have office management permissions
        if self.role == 'office_admin' and perm == 'manage_office':
            return True
            
        # Standard permissions for standard users
        if self.role in ['standard_user', 'office_admin']:
            standard_perms = [
                'view_person', 'add_person', 'change_person', 'delete_person',
                'view_church', 'add_church', 'change_church', 'delete_church',
                'view_task', 'add_task', 'change_task', 'delete_task',
                'view_communication', 'add_communication', 'change_communication', 'delete_communication',
            ]
            if perm in standard_perms:
                return True
                
        # Limited users have view-only permissions
        if self.role == 'limited_user':
            limited_perms = [
                'view_person', 'view_church', 'view_task', 'view_communication',
            ]
            if perm in limited_perms:
                return True
                
        # Fall back to default permission check
        return super().has_perm(perm, obj)


class GoogleToken(models.Model):
    """
    Stores Google OAuth tokens for users.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    access_token = models.TextField()
    refresh_token = models.TextField(blank=True, null=True)
    token_type = models.CharField(max_length=50, blank=True, null=True)
    expires_at = models.DateTimeField()
    scopes = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'google_tokens'
        indexes = [
            models.Index(fields=['user']),
        ]
    
    @property
    def is_expired(self):
        """Check if the token is expired."""
        return self.expires_at <= timezone.now()


class UserContactSyncSettings(models.Model):
    """
    User preferences for Google Contacts synchronization.
    """
    SYNC_CHOICES = [
        ('disabled', 'Disabled - No contact sync'),
        ('crm_only', 'CRM Only - Sync only contacts that exist in CRM'),
        ('all_contacts', 'All Contacts - Import all Google contacts to CRM'),
    ]
    
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='contact_sync_settings'
    )
    sync_preference = models.CharField(
        max_length=20,
        choices=SYNC_CHOICES,
        default='crm_only',
        help_text="Choose how Google contacts should be synchronized"
    )
    auto_sync_enabled = models.BooleanField(
        default=True,
        help_text="Enable automatic contact synchronization"
    )
    sync_frequency_hours = models.PositiveIntegerField(
        default=24,
        help_text="How often to sync contacts (in hours)"
    )
    last_sync_at = models.DateTimeField(
        blank=True, 
        null=True,
        help_text="When contacts were last synced"
    )
    sync_errors = models.JSONField(
        blank=True, 
        null=True,
        help_text="Any errors from the last sync attempt"
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_contact_sync_settings'
        verbose_name = 'Contact Sync Settings'
        verbose_name_plural = 'Contact Sync Settings'
    
    def __str__(self):
        return f"{self.user.username} - {self.get_sync_preference_display()}"
    
    def should_sync_now(self):
        """Check if it's time to sync based on frequency setting."""
        if not self.auto_sync_enabled or self.sync_preference == 'disabled':
            return False
        
        if not self.last_sync_at:
            return True
        
        from datetime import timedelta
        sync_interval = timedelta(hours=self.sync_frequency_hours)
        return timezone.now() - self.last_sync_at >= sync_interval
    
    def update_last_sync(self, errors=None):
        """Update the last sync timestamp and any errors."""
        self.last_sync_at = timezone.now()
        self.sync_errors = errors
        self.save(update_fields=['last_sync_at', 'sync_errors'])
