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
