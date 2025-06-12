from django.db import models


class Contact(models.Model):
    """
    Base Contact model for storing common contact information.
    
    This model represents the 'contacts' table in the Supabase database.
    Both Person and Church models inherit from this model.
    """
    # Primary Key
    id = models.AutoField(primary_key=True)  # Using AutoField to match nextval('contacts_id_seq'::regclass)
    
    # Basic Contact Information
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    church_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    image = models.CharField(max_length=255, blank=True, null=True)
    preferred_contact_method = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=255, blank=True, null=True)
    
    # Address Information
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=255, blank=True, null=True)
    state = models.CharField(max_length=255, blank=True, null=True)
    zip_code = models.CharField(max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    country = models.TextField(blank=True, null=True)
    
    # Notes
    notes = models.TextField(blank=True, null=True)
    initial_notes = models.TextField(blank=True, null=True)
    
    # Google Integration
    google_resource_name = models.CharField(max_length=255, blank=True, null=True)
    google_contact_id = models.CharField(max_length=255, blank=True, null=True)
    
    # Timestamps
    created_at = models.DateField(blank=True, null=True)
    updated_at = models.DateField(blank=True, null=True)
    date_created = models.DateField(blank=True, null=True)
    date_modified = models.DateField(blank=True, null=True)
    last_synced_at = models.DateField(blank=True, null=True)
    
    # Ownership
    office_id = models.IntegerField(blank=True, null=True)
    user_id = models.IntegerField(blank=True, null=True)  # Integer in contacts table
    
    # Conflict Management
    conflict_data = models.JSONField(blank=True, null=True)  # Using JSONField for jsonb type
    has_conflict = models.BooleanField(blank=True, null=True)
    
    class Meta:
        db_table = 'contacts'
        verbose_name = 'Contact'
        verbose_name_plural = 'Contacts'
    
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


class Person(Contact):
    """
    Person model for storing individual contact information.
    
    This model extends the Contact model and represents the 'people' table in Supabase.
    It has a one-to-one relationship with the Contact model through the primary key.
    """
    # Personal details
    title = models.CharField(max_length=255, blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    anniversary = models.DateField(blank=True, null=True)
    marital_status = models.CharField(max_length=255, blank=True, null=True)
    spouse_first_name = models.CharField(max_length=255, blank=True, null=True)
    spouse_last_name = models.CharField(max_length=255, blank=True, null=True)
    home_country = models.CharField(max_length=255, blank=True, null=True)
    languages = models.TextField(blank=True, null=True)
    
    # Professional details
    occupation = models.CharField(max_length=255, blank=True, null=True)
    employer = models.CharField(max_length=255, blank=True, null=True)
    skills = models.TextField(blank=True, null=True)
    interests = models.TextField(blank=True, null=True)
    
    # Church relationship
    church_id = models.IntegerField(blank=True, null=True)
    church_role = models.CharField(max_length=255, blank=True, null=True)
    is_primary_contact = models.BooleanField(blank=True, null=True)
    
    # Pipeline and status fields
    pipeline_stage = models.CharField(max_length=255, blank=True, null=True)
    people_pipeline = models.CharField(max_length=255, blank=True, null=True)
    priority = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    
    # Dates and tracking
    last_contact = models.DateField(blank=True, null=True)
    next_contact = models.DateField(blank=True, null=True)
    date_closed = models.DateField(blank=True, null=True)
    
    # Notes and metadata
    info_given = models.TextField(blank=True, null=True)
    desired_service = models.TextField(blank=True, null=True)
    reason_closed = models.TextField(blank=True, null=True)
    tags = models.TextField(blank=True, null=True)
    
    # Assignment and ownership
    assigned_to = models.CharField(max_length=255, blank=True, null=True)
    
    # Note: In Supabase, people.user_id is character varying while Contact.user_id is integer
    # Using people_user_id to avoid field clash with Contact.user_id
    people_user_id = models.CharField(max_length=255, blank=True, null=True, db_column='user_id')  # Firebase UID
    
    # Source information
    source = models.CharField(max_length=255, blank=True, null=True)
    referred_by = models.CharField(max_length=255, blank=True, null=True)
    
    # Social media
    website = models.CharField(max_length=255, blank=True, null=True)
    facebook = models.CharField(max_length=255, blank=True, null=True)
    twitter = models.CharField(max_length=255, blank=True, null=True)
    linkedin = models.CharField(max_length=255, blank=True, null=True)
    instagram = models.CharField(max_length=255, blank=True, null=True)
    
    # Integration fields
    virtuous = models.BooleanField(blank=True, null=True)
    
    class Meta:
        db_table = 'people'
        verbose_name = 'Person'
        verbose_name_plural = 'People'
        ordering = ['last_name', 'first_name']
    
    @property
    def name(self):
        """Return the full name of the person."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return ""
    
    def get_absolute_url(self):
        """Return the URL to access a detail record for this person."""
        from django.urls import reverse
        return reverse('contacts:person_detail', args=[str(self.id)])
