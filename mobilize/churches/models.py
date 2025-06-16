from django.db import models
from django.utils import timezone # If needed for default values
from mobilize.contacts.models import Contact


class Church(models.Model):
    """
    Church model for storing church organization information.
    
    This model represents church organizations in the CRM system.
    Matches the 'churches' table in the Supabase database.
    It extends the Contact model via a OneToOneField.
    """
    contact = models.OneToOneField(
        Contact,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='church_details'
    )

    # Church-specific fields
    name = models.CharField(max_length=255, blank=True, null=True, help_text="The official name of the church.")
    location = models.CharField(max_length=255, blank=True, null=True)
    denomination = models.CharField(max_length=100, blank=True, null=True)
    website = models.CharField(max_length=255, blank=True, null=True)  # Using CharField to match Supabase
    year_founded = models.IntegerField(blank=True, null=True)

    # Size Information
    congregation_size = models.IntegerField(blank=True, null=True)
    weekly_attendance = models.IntegerField(blank=True, null=True)

    # Fields from mobilize-prompt-django.md
    service_times = models.JSONField(blank=True, null=True, help_text="e.g., Sunday 9am, Wednesday 7pm")
    # pastor_name, pastor_email, pastor_phone are covered by Senior Pastor section below for now
    facilities = models.JSONField(blank=True, null=True, help_text="Details about church facilities.")
    ministries = models.JSONField(blank=True, null=True, help_text="List or details of church ministries.")
    primary_language = models.CharField(max_length=50, blank=True, null=True)
    secondary_languages = models.JSONField(blank=True, null=True, help_text="Other languages used in services/ministries.")

    # Senior Pastor Information
    pastor_name = models.CharField(max_length=200, blank=True, null=True, help_text="Name of the senior pastor (replaces senior_pastor_name).")
    senior_pastor_first_name = models.CharField(max_length=255, blank=True, null=True)
    senior_pastor_last_name = models.CharField(max_length=255, blank=True, null=True)
    pastor_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Phone number of the senior pastor (replaces senior_pastor_phone).")
    pastor_email = models.EmailField(max_length=255, blank=True, null=True, help_text="Email of the senior pastor (replaces senior_pastor_email).")

    # Missions Pastor Information
    missions_pastor_first_name = models.CharField(max_length=255, blank=True, null=True)
    missions_pastor_last_name = models.CharField(max_length=255, blank=True, null=True)
    mission_pastor_phone = models.CharField(max_length=255, blank=True, null=True)  # Match Supabase field name
    mission_pastor_email = models.CharField(max_length=255, blank=True, null=True)  # Match Supabase field name

    # Primary Contact Information
    primary_contact_first_name = models.CharField(max_length=255, blank=True, null=True)
    primary_contact_last_name = models.CharField(max_length=255, blank=True, null=True)
    primary_contact_phone = models.CharField(max_length=255, blank=True, null=True)
    primary_contact_email = models.CharField(max_length=255, blank=True, null=True)
    main_contact_id = models.IntegerField(blank=True, null=True)

    # Church-specific pipeline field (generic pipeline_stage is on Contact)
    church_pipeline = models.CharField(max_length=255, blank=True, null=True)
    
    # Integration flag
    virtuous = models.BooleanField(blank=True, null=True)
    
    # Church-specific fields
    info_given = models.TextField(blank=True, null=True)
    
    # Note: The following fields are now on Contact model:
    # - priority, status, pipeline_stage
    # - assigned_to (via user field)
    # - date_closed (via status)
    # - source, referred_by (can use custom_fields)
    # - reason_closed (can use notes)
    # - owner_id (via user field)
    # - office_id (via office field)

    class Meta:
        db_table = 'churches'
        verbose_name = 'Church'
        verbose_name_plural = 'Churches'
        ordering = ['name'] # Order by church name
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['church_pipeline']),
            models.Index(fields=['denomination']),
            models.Index(fields=['congregation_size']),
        ]

    def __str__(self):
        return self.name if self.name else self.contact.church_name or f"Church (Contact ID: {self.contact_id})"

    @property
    def full_address(self):
        """Return the full address as a formatted string."""
        # Address fields are on the related Contact model
        return self.contact.full_address

    def get_absolute_url(self):
        """Return the URL to access a detail record for this church."""
        from django.urls import reverse
        return reverse('churches:church_detail', args=[str(self.contact_id)])
