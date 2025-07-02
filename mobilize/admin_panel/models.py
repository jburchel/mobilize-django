from django.db import models
from django.utils import timezone as django_timezone
from django.conf import settings
from django.db.models import Q


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
        from django.contrib.auth import get_user_model
        User = get_user_model()
        # Get user_ids from this office
        user_ids = self.useroffice_set.values_list('user_id', flat=True)
        # Convert to integers and count admin users
        try:
            int_user_ids = [int(uid) for uid in user_ids if uid]
            return User.objects.filter(
                id__in=int_user_ids,
                role__in=['super_admin', 'office_admin']
            ).count()
        except (ValueError, TypeError):
            return 0


class UserOfficeManager(models.Manager):
    """
    Custom manager for UserOffice that handles user_id type conversion.
    
    This is needed because the user_id column in the database is VARCHAR,
    but Django's User model has an integer primary key.
    """
    def get_queryset(self):
        """Override to handle string conversion when needed."""
        return super().get_queryset()
    
    def filter(self, **kwargs):
        """Override filter to convert user_id to string if needed."""
        if 'user_id' in kwargs and kwargs['user_id'] is not None:
            kwargs['user_id'] = str(kwargs['user_id'])
        if 'user' in kwargs and hasattr(kwargs['user'], 'id'):
            # Convert the user object to user_id string
            kwargs['user_id'] = str(kwargs['user'].id)
            del kwargs['user']
        return super().filter(**kwargs)
    
    def get(self, **kwargs):
        """Override get to convert user_id to string if needed."""
        if 'user_id' in kwargs and kwargs['user_id'] is not None:
            kwargs['user_id'] = str(kwargs['user_id'])
        if 'user' in kwargs and hasattr(kwargs['user'], 'id'):
            # Convert the user object to user_id string
            kwargs['user_id'] = str(kwargs['user'].id)
            del kwargs['user']
        return super().get(**kwargs)


class UserOffice(models.Model):
    """
    Junction model for User-Office relationship.
    
    Allows users to be assigned to multiple offices.
    Office permissions are derived from the user's overall role.
    
    Note: user_id is stored as VARCHAR in the database due to legacy reasons.
    """
    user_id = models.CharField(max_length=50, db_column='user_id')  # Explicitly define as CharField to match database
    office = models.ForeignKey(Office, on_delete=models.CASCADE, db_column='office_id')
    is_primary = models.BooleanField(default=False)
    permissions = models.JSONField(blank=True, null=True)
    assigned_at = models.DateTimeField(default=django_timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = UserOfficeManager()
    
    class Meta:
        db_table = 'user_offices'
        unique_together = ('user_id', 'office')
        indexes = [
            models.Index(fields=['user_id']),
            models.Index(fields=['office']),
        ]
    
    @property
    def user(self):
        """Get the User object for this UserOffice."""
        from django.contrib.auth import get_user_model
        User = get_user_model()
        try:
            return User.objects.get(id=int(self.user_id))
        except (User.DoesNotExist, ValueError):
            return None
    
    def __str__(self):
        user = self.user
        if user:
            return f"{user.username} - {self.office.name}"
        return f"User {self.user_id} - {self.office.name}"
    
    def save(self, *args, **kwargs):
        """Override save to ensure only one primary office per user."""
        if self.is_primary:
            # Set all other offices for this user as non-primary
            UserOffice.objects.filter(user_id=self.user_id, is_primary=True).update(is_primary=False)
        super().save(*args, **kwargs)
