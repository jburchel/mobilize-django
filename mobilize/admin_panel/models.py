from django.db import models
from django.utils import timezone as django_timezone
from django.conf import settings


class Office(models.Model):
    """
    Represents a physical or virtual office location within the organization.
    
    Offices can have multiple users assigned to them with different roles.
    """
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = models.CharField(max_length=50, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    postal_code = models.CharField(max_length=20, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    timezone_name = models.CharField(max_length=50, default='UTC')
    settings = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(default=django_timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['code']),
        ]
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def user_count(self):
        """Get the number of users assigned to this office."""
        return self.useroffice_set.count()
    
    @property
    def admin_count(self):
        """Get the number of admin users assigned to this office."""
        return self.useroffice_set.filter(role='office_admin').count()


class UserOffice(models.Model):
    """
    Junction model for User-Office relationship.
    
    Allows users to be assigned to multiple offices with different roles.
    """
    ROLE_CHOICES = (
        ('office_admin', 'Office Admin'),
        ('standard_user', 'Standard User'),
        ('limited_user', 'Limited User'),
    )
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    office = models.ForeignKey(Office, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='standard_user')
    is_primary = models.BooleanField(default=False)
    permissions = models.JSONField(blank=True, null=True)
    assigned_at = models.DateTimeField(default=django_timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'user_offices'
        unique_together = ('user', 'office')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['office']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.office.name} ({self.get_role_display()})"
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one primary office per user."""
        if self.is_primary:
            # Set all other offices for this user as non-primary
            UserOffice.objects.filter(user=self.user, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)
