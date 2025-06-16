from django.db import models
from django.utils import timezone
from django.conf import settings


# Import the main pipeline stages from the pipeline app
from mobilize.pipeline.models import MAIN_PEOPLE_PIPELINE_STAGES, MAIN_CHURCH_PIPELINE_STAGES

# Combined choices for form validation
ALL_PIPELINE_STAGES = list(set(MAIN_PEOPLE_PIPELINE_STAGES + MAIN_CHURCH_PIPELINE_STAGES))


class Contact(models.Model):
    """
    Base Contact model for storing common contact information.
    
    This model aligns with the 'contacts' table structure from mobilize-prompt-django.md.
    """
    TYPE_CHOICES = (
        ('person', 'Person'),
        ('church', 'Church'),
    )
    type = models.CharField(max_length=20, choices=TYPE_CHOICES, help_text="Type of contact: Person or Church")
    
    # Basic Contact Information
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    church_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(max_length=255, blank=True, null=True, unique=True, help_text="Primary email address, unique if provided.")
    phone = models.CharField(max_length=20, blank=True, null=True, help_text="Primary phone number.")
    image = models.CharField(max_length=255, blank=True, null=True)
    preferred_contact_method = models.CharField(max_length=255, blank=True, null=True)
    
    # Address Information
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True) # Legacy/combined address field
    country = models.CharField(max_length=100, blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True, help_text="General notes about the contact.")
    initial_notes = models.TextField(blank=True, null=True) # Consider merging into 'notes'
    
    # Google Integration
    google_resource_name = models.CharField(max_length=255, blank=True, null=True)
    google_contact_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    date_created = models.DateField(blank=True, null=True) # Legacy, prefer created_at
    date_modified = models.DateField(blank=True, null=True) # Legacy, prefer updated_at
    last_synced_at = models.DateTimeField(blank=True, null=True)
    
    # Ownership
    office = models.ForeignKey(
        'admin_panel.Office', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, 
        related_name='contacts_by_office',
        db_column='office_id' # Matches Supabase schema column name
    )
    user = models.ForeignKey( # Renamed from user_id to align with Django conventions
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, # Or models.CASCADE as per mobilize-prompt-django.md
        null=True, blank=True, 
        related_name='created_contacts', # Or 'owned_contacts'
        db_column='user_id' # Matches Supabase schema column name
    )
    
    # Conflict Management
    conflict_data = models.JSONField(blank=True, null=True)  # Using JSONField for jsonb type
    has_conflict = models.BooleanField(blank=True, null=True)

    # Fields from mobilize-prompt-django.md for Contact
    # NOTE: pipeline_stage removed - now tracked via PipelineContact relationship
    priority = models.CharField(max_length=20, blank=True, null=True, help_text="Priority level (e.g., low, medium, high).")
    status = models.CharField(max_length=20, default='active', help_text="Status of the contact (e.g., active, inactive).")
    last_contact_date = models.DateTimeField(blank=True, null=True, help_text="Date of last interaction.")
    next_contact_date = models.DateTimeField(blank=True, null=True, help_text="Scheduled date for next interaction.")
    tags = models.JSONField(blank=True, null=True, help_text="JSON field for storing tags.") # Overwrites existing tags field
    custom_fields = models.JSONField(blank=True, null=True, help_text="JSON field for custom data.")
    
    class Meta:
        db_table = 'contacts'
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['office']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.church_name:
            return self.church_name
        return f"Contact {self.id}"
    
    @property
    def full_address(self):
        """Return the full address as a formatted string."""
        parts = []
        if self.street_address:
            parts.append(self.street_address)
        
        city_state = []
        if self.city:
            city_state.append(self.city)
        if self.state:
            city_state.append(self.state)
        if city_state:
            parts.append(", ".join(city_state))
        
        if self.zip_code:
            parts.append(self.zip_code)
        
        if self.country and self.country.lower() != "usa" and self.country.lower() != "united states":
            parts.append(self.country)
            
        return ", ".join(parts) if parts else (self.address if self.address else "")
    
    def get_main_pipeline(self):
        """Get the main pipeline for this contact type."""
        from mobilize.pipeline.models import Pipeline
        if self.type == 'person':
            return Pipeline.get_main_people_pipeline()
        elif self.type == 'church':
            return Pipeline.get_main_church_pipeline()
        return None
    
    def get_pipeline_contact(self):
        """Get the PipelineContact entry for this contact."""
        from mobilize.pipeline.models import PipelineContact
        try:
            return self.pipeline_entries.filter(
                pipeline=self.get_main_pipeline()
            ).first()
        except:
            return None
    
    def get_current_pipeline_stage(self):
        """Get the current pipeline stage for this contact."""
        pipeline_contact = self.get_pipeline_contact()
        return pipeline_contact.current_stage if pipeline_contact else None
    
    def get_pipeline_stage_name(self):
        """Get the name of the current pipeline stage."""
        stage = self.get_current_pipeline_stage()
        return stage.name if stage else None
    
    def get_pipeline_stage_code(self):
        """Get the code of the current pipeline stage (for templates)."""
        stage = self.get_current_pipeline_stage()
        if not stage:
            return None
        
        # Convert stage name to lowercase code for template comparisons
        name_to_code = {
            'Promotion': 'promotion',
            'Information': 'information', 
            'Invitation': 'invitation',
            'Confirmation': 'confirmation',
            'Automation': 'automation',
            'EN42': 'en42',
        }
        return name_to_code.get(stage.name, stage.name.lower())
    
    def set_pipeline_stage(self, stage_name):
        """Set the pipeline stage for this contact."""
        from mobilize.pipeline.models import PipelineContact, PipelineStage
        
        main_pipeline = self.get_main_pipeline()
        if not main_pipeline:
            raise ValueError(f"No main pipeline found for contact type: {self.type}")
        
        # Find the stage by name
        try:
            stage = main_pipeline.stages.get(name=stage_name)
        except PipelineStage.DoesNotExist:
            available_stages = [s.name for s in main_pipeline.stages.all()]
            raise ValueError(f"Stage '{stage_name}' not found. Available stages: {available_stages}")
        
        # Get or create PipelineContact using the direct contact relationship
        pipeline_contact, created = PipelineContact.objects.get_or_create(
            contact=self,
            pipeline=main_pipeline,
            defaults={
                'contact_type': self.type,
                'current_stage': stage
            }
        )
        
        if not created:
            # Update existing stage
            pipeline_contact.current_stage = stage
            pipeline_contact.save()
        
        return pipeline_contact
    
    def ensure_pipeline_assignment(self):
        """Ensure this contact is assigned to their main pipeline."""
        pipeline_contact = self.get_pipeline_contact()
        if not pipeline_contact:
            # Assign to first stage of main pipeline
            main_pipeline = self.get_main_pipeline()
            if main_pipeline:
                first_stage = main_pipeline.stages.order_by('order').first()
                if first_stage:
                    self.set_pipeline_stage(first_stage.name)


class Person(models.Model):
    """
    Person model for storing individual contact information.
    
    This model links to a Contact record via a OneToOneField.
    Fields here are specific to individuals.
    """
    contact = models.OneToOneField(
        Contact,
        on_delete=models.CASCADE,
        primary_key=True,
        related_name='person_details'
    )

    # Personal details
    # first_name, last_name are on Contact model
    title = models.CharField(max_length=50, blank=True, null=True)
    preferred_name = models.CharField(max_length=100, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    anniversary = models.DateField(blank=True, null=True)
    marital_status = models.CharField(max_length=20, blank=True, null=True)
    spouse_first_name = models.CharField(max_length=255, blank=True, null=True)
    spouse_last_name = models.CharField(max_length=255, blank=True, null=True)
    home_country = models.CharField(max_length=100, blank=True, null=True)
    languages = models.JSONField(blank=True, null=True) # Changed to JSONField as per mobilize-prompt-django.md
    
    # Professional details
    profession = models.CharField(max_length=100, blank=True, null=True) # Renamed from occupation
    organization = models.CharField(max_length=255, blank=True, null=True) # Renamed from employer
    # skills, interests are not in mobilize-prompt-django.md for Person, consider custom_fields on Contact
    
    # Church relationship
    primary_church = models.ForeignKey(
        'churches.Church', 
        on_delete=models.SET_NULL, 
        null=True, blank=True, # Added blank=True
        related_name='members'
    ) # Renamed from church_id
    church_role = models.CharField(max_length=100, blank=True, null=True)
    # is_primary_contact - consider if this is still needed or part of a different relationship
    
    # Social media
    linkedin_url = models.URLField(max_length=255, blank=True, null=True)
    facebook_url = models.URLField(max_length=255, blank=True, null=True)
    twitter_url = models.URLField(max_length=255, blank=True, null=True)
    instagram_url = models.URLField(max_length=255, blank=True, null=True)
    
    # Integration fields
    # virtuous - not in mobilize-prompt-django.md for Person
    google_contact_id = models.CharField(max_length=255, blank=True, null=True) # From mobilize-prompt-django.md
    
    class Meta:
        db_table = 'people'
        verbose_name = 'Person'
        verbose_name_plural = 'People'
        ordering = ['contact__last_name', 'contact__first_name'] # Order by related Contact fields
    
    @property
    def name(self):
        """Return the full name of the person."""
        if self.contact.first_name and self.contact.last_name:
            return f"{self.contact.first_name} {self.contact.last_name}"
        elif self.contact.first_name:
            return self.contact.first_name
        elif self.contact.last_name:
            return self.contact.last_name
        return ""
    
    def get_absolute_url(self):
        """Return the URL to access a detail record for this person."""
        from django.urls import reverse
        return reverse('contacts:person_detail', args=[str(self.contact_id)])
