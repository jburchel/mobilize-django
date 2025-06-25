from django.db import models
from django.conf import settings
from django.utils import timezone
from mobilize.contacts.models import Person
from mobilize.churches.models import Church
from mobilize.admin_panel.models import Office


class EmailTemplate(models.Model):
    """Model for storing reusable email templates"""
    name = models.CharField(max_length=100)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    is_html = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_templates'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    category = models.CharField(max_length=50, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'email_templates' # Align with supabase_schema.md
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
        ]
    
    def __str__(self):
        return self.name


class EmailSignature(models.Model):
    """Model for storing user email signatures"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='email_signatures'
    )
    name = models.CharField(max_length=50)
    content = models.TextField()
    logo_url = models.URLField(max_length=255, blank=True, null=True, help_text="URL to logo image for signature")
    logo_file = models.ImageField(upload_to='signature_logos/', blank=True, null=True, help_text="Upload logo image file (PNG, JPG)")
    is_default = models.BooleanField(default=False)
    is_html = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'email_signatures' # Align with supabase_schema.md
        ordering = ['-is_default', 'name']
        indexes = [
            models.Index(fields=['user', 'is_default']),
        ]
    
    @property
    def logo_source(self):
        """Return the logo file URL if available, otherwise the logo URL"""
        if self.logo_file:
            return self.logo_file.url
        return self.logo_url
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.name}"
    
    def save(self, *args, **kwargs):
        # If this signature is set as default, unset any other default signatures for this user
        if self.is_default:
            EmailSignature.objects.filter(
                user=self.user, 
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        
        # If this is the user's first signature, make it default
        if not self.pk and not EmailSignature.objects.filter(user=self.user).exists():
            self.is_default = True
            
        super().save(*args, **kwargs)


class Communication(models.Model):
    """Model for tracking all communications with contacts and churches.
    
    Matches the 'communications' table in the Supabase database.
    """
    # Basic Information
    id = models.AutoField(primary_key=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    message = models.CharField(max_length=255, blank=True, null=True)
    subject = models.CharField(max_length=255, blank=True, null=True)
    direction = models.CharField(max_length=255, blank=True, null=True)
    
    # Dates and Times
    date = models.DateField(blank=True, null=True)
    date_sent = models.DateTimeField(blank=True, null=True)
    
    # Related Entities
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=True, null=True, related_name='person_communications', db_column='person_id')
    church = models.ForeignKey(Church, on_delete=models.SET_NULL, blank=True, null=True, related_name='church_communications', db_column='church_id')
    
    # Gmail Integration
    gmail_message_id = models.CharField(max_length=255, blank=True, null=True)
    gmail_thread_id = models.CharField(max_length=255, blank=True, null=True)
    email_status = models.CharField(max_length=255, blank=True, null=True)
    attachments = models.CharField(max_length=255, blank=True, null=True)
    sender = models.CharField(max_length=255, blank=True, null=True)
    
    # Assignment and Ownership
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name='communications')
    owner_id = models.IntegerField(blank=True, null=True)  # Legacy user ID
    office = models.ForeignKey(Office, on_delete=models.SET_NULL, blank=True, null=True, related_name='communications', db_column='office_id')
    
    # Email processing fields for Celery tasks
    content = models.TextField(blank=True, null=True, help_text="Email body content")
    status = models.CharField(max_length=50, default='pending', choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('sent', 'Sent'),
        ('delivered', 'Delivered'),
        ('failed', 'Failed'),
    ])
    external_id = models.CharField(max_length=255, blank=True, null=True, help_text="External message ID (e.g., Gmail message ID)")
    error_message = models.TextField(blank=True, null=True, help_text="Error message if sending failed")
    template_used = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, blank=True, null=True, related_name='communications')
    cc_recipients = models.TextField(blank=True, null=True, help_text="CC recipients as comma-separated emails")
    bcc_recipients = models.TextField(blank=True, null=True, help_text="BCC recipients as comma-separated emails")
    is_notification = models.BooleanField(default=False, help_text="Whether this is a system notification")
    archived = models.BooleanField(default=False, help_text="Whether this communication is archived")
    
    # Google Calendar Integration
    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    google_meet_link = models.CharField(max_length=255, blank=True, null=True)
    last_synced_at = models.DateTimeField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateField(blank=True, null=True, default=timezone.now)
    updated_at = models.DateField(blank=True, null=True, auto_now=True)
    
    class Meta:
        db_table = 'communications'
        verbose_name = 'Communication'
        verbose_name_plural = 'Communications'
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date'], name='comm_date_idx'),
            models.Index(fields=['type'], name='comm_type_idx'),
            models.Index(fields=['user'], name='comm_user_idx'),
            models.Index(fields=['email_status'], name='comm_email_status_idx'),
            models.Index(fields=['user', 'date']),         # Composite for user communications
            models.Index(fields=['type', 'date']),            # Composite for type filtering
            models.Index(fields=['office', 'date']),          # Composite for office communications
            models.Index(fields=['gmail_message_id']),        # For Gmail sync lookups
            models.Index(fields=['status']),                  # For Celery task processing
        ]
    
    def __str__(self):
        return self.subject if self.subject else f"Communication {self.id}"


class EmailAttachment(models.Model):
    """Model for storing email attachments
    
    Note: This model is for Django admin interface only and doesn't correspond
    to a table in the Supabase database. Attachments in Supabase are stored as
    text in the 'attachments' column of the communications table.
    """
    communication = models.ForeignKey(
        Communication,
        on_delete=models.CASCADE,
        related_name='email_attachments'
    )
    file = models.FileField(upload_to='email_attachments/%Y/%m/%d/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100)
    size = models.PositiveIntegerField()  # Size in bytes
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'django_email_attachments'
    
    def __str__(self):
        return self.filename
