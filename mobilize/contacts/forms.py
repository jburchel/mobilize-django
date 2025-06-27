from django import forms
from django.core.validators import FileExtensionValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Div

from .models import Person, Contact
from mobilize.churches.models import Church, ChurchMembership


class PersonForm(forms.ModelForm):
    """Form for creating and editing Person records."""
    
    # Contact fields that will be handled separately
    first_name = forms.CharField(max_length=255, required=False, label="First Name")
    last_name = forms.CharField(max_length=255, required=False, label="Last Name")
    email = forms.EmailField(max_length=255, required=False, label="Email")
    phone = forms.CharField(max_length=20, required=False, label="Phone")
    CONTACT_METHOD_CHOICES = [
        ('', '-- Select Method --'),
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('text', 'Text'),
    ]
    
    preferred_contact_method = forms.ChoiceField(
        choices=CONTACT_METHOD_CHOICES, 
        required=False, 
        label="Preferred Contact Method"
    )
    street_address = forms.CharField(max_length=255, required=False, label="Street Address")
    city = forms.CharField(max_length=255, required=False, label="City")
    state = forms.CharField(max_length=255, required=False, label="State")
    zip_code = forms.CharField(max_length=255, required=False, label="ZIP Code")
    country = forms.CharField(max_length=100, required=False, label="Country")
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    initial_notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}), 
        required=False,
        label="Initial Notes",
        help_text="Notes from first contact or initial interaction"
    )
    pipeline_stage = forms.ChoiceField(choices=[], required=False)
    priority = forms.ChoiceField(choices=Contact.PRIORITY_CHOICES, required=False)
    status = forms.ChoiceField(choices=Contact.STATUS_CHOICES, required=False)
    tags = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    # Override church-related fields to use proper choices
    primary_church = forms.ModelChoiceField(
        queryset=Church.objects.all(),
        required=False,
        empty_label="-- Select Church --",
        label="Primary Church"
    )
    church_role = forms.ChoiceField(
        choices=[('', '-- Select Role --')] + ChurchMembership.ROLE_CHOICES,
        required=False,
        label="Church Role"
    )
    
    # Override languages field to handle comma-separated input
    languages = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2, 'placeholder': 'Enter languages separated by commas (e.g., English, Spanish, French)'}),
        required=False,
        help_text="Enter languages separated by commas"
    )
    
    class Meta:
        model = Person
        fields = [
            # Person-specific fields only
            'title', 'preferred_name', 'birthday', 'anniversary', 'marital_status', 
            'spouse_first_name', 'spouse_last_name', 'home_country', 
            'profession', 'organization',
            'info_given', 'desired_service',
            'linkedin_url', 'facebook_url', 'twitter_url', 'instagram_url',
            'google_contact_id'
        ]
        widgets = {
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'anniversary': forms.DateInput(attrs={'type': 'date'}),
            'info_given': forms.Textarea(attrs={'rows': 3}),
            'desired_service': forms.Textarea(attrs={'rows': 3}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up pipeline stage choices for person contacts
        from mobilize.pipeline.models import Pipeline
        main_pipeline = Pipeline.get_main_people_pipeline()
        if main_pipeline:
            stage_choices = [('', '--- Select Stage ---')]
            stage_choices.extend([
                (stage.name, stage.name) for stage in main_pipeline.stages.all().order_by('order')
            ])
            self.fields['pipeline_stage'].choices = stage_choices
        
        # If we have an instance, populate Contact fields
        if self.instance and hasattr(self.instance, 'contact'):
            contact = self.instance.contact
            self.fields['first_name'].initial = contact.first_name
            self.fields['last_name'].initial = contact.last_name
            self.fields['email'].initial = contact.email
            self.fields['phone'].initial = contact.phone
            self.fields['preferred_contact_method'].initial = contact.preferred_contact_method
            self.fields['street_address'].initial = contact.street_address
            self.fields['city'].initial = contact.city
            self.fields['state'].initial = contact.state
            self.fields['zip_code'].initial = contact.zip_code
            self.fields['country'].initial = contact.country
            self.fields['notes'].initial = contact.notes
            self.fields['initial_notes'].initial = contact.initial_notes
            # Get pipeline stage from the relationship system
            current_stage = contact.get_current_pipeline_stage()
            self.fields['pipeline_stage'].initial = current_stage.name if current_stage else None
            self.fields['priority'].initial = contact.priority
            self.fields['status'].initial = contact.status
            # Handle tags - convert list to string for display
            if contact.tags:
                if isinstance(contact.tags, list):
                    self.fields['tags'].initial = ', '.join(contact.tags)
                else:
                    self.fields['tags'].initial = contact.tags
            else:
                self.fields['tags'].initial = ''
                
            # Populate church relationship fields from ChurchMembership
            primary_membership = self.instance.church_memberships.filter(
                is_primary_contact=True, 
                status='active'
            ).first()
            if primary_membership:
                self.fields['primary_church'].initial = primary_membership.church
                self.fields['church_role'].initial = primary_membership.role
            elif self.instance.church_memberships.filter(status='active').exists():
                # If no primary contact but has active memberships, use the first one
                first_membership = self.instance.church_memberships.filter(status='active').first()
                self.fields['primary_church'].initial = first_membership.church
                self.fields['church_role'].initial = first_membership.role
                
            # Handle languages field - convert JSON list to comma-separated string
            if self.instance.languages:
                if isinstance(self.instance.languages, list):
                    self.fields['languages'].initial = ', '.join(self.instance.languages)
                else:
                    self.fields['languages'].initial = str(self.instance.languages)
        
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-grid'
        
        self.helper.layout = Layout(
            # Basic Information Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-primary text-white"><h5 class="mb-0"><i class="fas fa-user me-2"></i>Basic Information</h5></div><div class="card-body">'),
                Row(
                    Column('first_name', css_class='col-md-6 mb-3'),
                    Column('last_name', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('title', css_class='col-md-6 mb-3'),
                    Column('preferred_name', css_class='col-md-6 mb-3'),
                ),
                HTML('</div></div>')
            ),
            
            # Contact Information Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-success text-white"><h5 class="mb-0"><i class="fas fa-address-card me-2"></i>Contact Information</h5></div><div class="card-body">'),
                Row(
                    Column('street_address', css_class='col-md-8 mb-3'),
                    Column('country', css_class='col-md-4 mb-3'),
                ),
                Row(
                    Column('city', css_class='col-md-4 mb-3'),
                    Column('state', css_class='col-md-4 mb-3'),
                    Column('zip_code', css_class='col-md-4 mb-3'),
                ),
                Row(
                    Column('email', css_class='col-md-6 mb-3'),
                    Column('phone', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('preferred_contact_method', css_class='col-md-6 mb-3'),
                    Column(HTML(''), css_class='col-md-6'),  # Empty spacer
                ),
                HTML('</div></div>')
            ),
            
            # Personal Details Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-info text-white"><h5 class="mb-0"><i class="fas fa-heart me-2"></i>Personal Details</h5></div><div class="card-body">'),
                Row(
                    Column('birthday', css_class='col-md-6 mb-3'),
                    Column('anniversary', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('marital_status', css_class='col-md-6 mb-3'),
                    Column('home_country', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('spouse_first_name', css_class='col-md-6 mb-3'),
                    Column('spouse_last_name', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('languages', css_class='col-md-6 mb-3'),
                    Column(HTML(''), css_class='col-md-6'),  # Empty spacer
                ),
                HTML('</div></div>')
            ),
            
            # Professional Information Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-warning text-dark"><h5 class="mb-0"><i class="fas fa-briefcase me-2"></i>Professional Information</h5></div><div class="card-body">'),
                Row(
                    Column('profession', css_class='col-md-6 mb-3'),
                    Column('organization', css_class='col-md-6 mb-3'),
                ),
                HTML('</div></div>')
            ),
            
            # Mission/Service Information Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-success text-white"><h5 class="mb-0"><i class="fas fa-globe me-2"></i>Mission & Service</h5></div><div class="card-body">'),
                Row(
                    Column('info_given', css_class='col-md-6 mb-3'),
                    Column('desired_service', css_class='col-md-6 mb-3'),
                ),
                HTML('</div></div>')
            ),
            
            # Church Relationship Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-purple text-white"><h5 class="mb-0"><i class="fas fa-church me-2"></i>Church Relationship</h5></div><div class="card-body">'),
                Row(
                    Column('primary_church', css_class='col-md-8 mb-3'),
                    Column('church_role', css_class='col-md-4 mb-3'),
                ),
                HTML('</div></div>')
            ),
            
            # Status & Pipeline Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-secondary text-white"><h5 class="mb-0"><i class="fas fa-flag me-2"></i>Status & Pipeline</h5></div><div class="card-body">'),
                Row(
                    Column('pipeline_stage', css_class='col-md-4 mb-3'),
                    Column('priority', css_class='col-md-4 mb-3'),
                    Column('status', css_class='col-md-4 mb-3'),
                ),
                HTML('</div></div>')
            ),
            
            # Social Media Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-gradient text-white"><h5 class="mb-0"><i class="fas fa-share-alt me-2"></i>Social Media</h5></div><div class="card-body">'),
                Row(
                    Column('facebook_url', css_class='col-md-6 mb-3'),
                    Column('twitter_url', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('linkedin_url', css_class='col-md-6 mb-3'),
                    Column('instagram_url', css_class='col-md-6 mb-3'),
                ),
                HTML('</div></div>')
            ),
            
            # Notes & Tags Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-dark text-white"><h5 class="mb-0"><i class="fas fa-sticky-note me-2"></i>Notes & Tags</h5></div><div class="card-body">'),
                'initial_notes',
                'notes',
                'tags',
                HTML('</div></div>')
            ),
            
            # Action Buttons
            Div(
                Submit('submit', 'Save Person', css_class='btn btn-primary btn-lg me-3'),
                HTML('<a href="{% if person %}{% url \'contacts:person_detail\' person.pk %}{% else %}{% url \'contacts:person_list\' %}{% endif %}" class="btn btn-secondary btn-lg">Cancel</a>'),
                css_class='text-center mt-4 mb-4'
            )
        )
    
    def save(self, commit=True, user=None, office=None):
        # Handle Contact creation/update
        if self.instance.pk:
            # Editing existing person
            contact = self.instance.contact
        else:
            # Creating new person
            contact = Contact(type='person')
        
        # Update contact fields
        contact.first_name = self.cleaned_data.get('first_name')
        contact.last_name = self.cleaned_data.get('last_name')
        contact.email = self.cleaned_data.get('email')
        contact.phone = self.cleaned_data.get('phone')
        contact.preferred_contact_method = self.cleaned_data.get('preferred_contact_method')
        contact.street_address = self.cleaned_data.get('street_address')
        contact.city = self.cleaned_data.get('city')
        contact.state = self.cleaned_data.get('state')
        contact.zip_code = self.cleaned_data.get('zip_code')
        contact.country = self.cleaned_data.get('country')
        contact.notes = self.cleaned_data.get('notes')
        contact.initial_notes = self.cleaned_data.get('initial_notes')
        contact.priority = self.cleaned_data.get('priority')
        contact.status = self.cleaned_data.get('status') or 'active'
        
        # Set user and office for new contacts
        if not self.instance.pk and user:
            contact.user = user
        if not self.instance.pk and office:
            contact.office = office
        
        # Handle tags - convert string to list if needed
        tags_value = self.cleaned_data.get('tags')
        if tags_value and isinstance(tags_value, str):
            # Convert comma-separated string to list
            contact.tags = [tag.strip() for tag in tags_value.split(',') if tag.strip()]
        else:
            contact.tags = tags_value
        
        if commit:
            contact.save()
            if not self.instance.pk:
                # Only set contact for new instances
                self.instance.contact = contact
            
            # Handle pipeline stage using the relationship system
            pipeline_stage_name = self.cleaned_data.get('pipeline_stage')
            if pipeline_stage_name:
                try:
                    contact.set_pipeline_stage(pipeline_stage_name)
                except ValueError:
                    # If stage doesn't exist, just skip it for now
                    pass
            
            # Handle languages field - convert comma-separated string to JSON list
            languages_input = self.cleaned_data.get('languages')
            if languages_input:
                # Split by comma and clean up whitespace
                languages_list = [lang.strip() for lang in languages_input.split(',') if lang.strip()]
                self.instance.languages = languages_list if languages_list else None
            else:
                self.instance.languages = None
            
            person = super().save(commit=True)
            
            # Handle church membership relationship
            primary_church = self.cleaned_data.get('primary_church')
            church_role = self.cleaned_data.get('church_role')
            
            if primary_church and church_role:
                # Create or update ChurchMembership
                membership, created = ChurchMembership.objects.get_or_create(
                    person=person,
                    church=primary_church,
                    defaults={
                        'role': church_role,
                        'is_primary_contact': True,  # Assume primary church = primary contact
                        'status': 'active'
                    }
                )
                if not created:
                    # Update existing membership
                    membership.role = church_role
                    membership.status = 'active'
                    membership.is_primary_contact = True
                    membership.save()
                
                # Make sure this is the only primary contact for this church
                ChurchMembership.objects.filter(
                    church=primary_church,
                    is_primary_contact=True
                ).exclude(person=person).update(is_primary_contact=False)
                
            elif not primary_church and not church_role:
                # If both are cleared, remove any existing memberships
                person.church_memberships.filter(is_primary_contact=True).update(status='inactive')
            
            return person
        else:
            if not self.instance.pk:
                self.instance.contact = contact
            return super().save(commit=False)



class ImportContactsForm(forms.Form):
    """Form for importing contacts from a CSV file."""
    
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Please upload a CSV file with contact information.',
        validators=[FileExtensionValidator(allowed_extensions=['csv'])]
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        self.helper.form_enctype = 'multipart/form-data'
        
        self.helper.layout = Layout(
            'csv_file',
            HTML('''
                <div class="alert alert-info mt-3">
                    <h5>CSV Format Instructions</h5>
                    <p>Your CSV file should have the following columns:</p>
                    <ul>
                        <li><strong>Required:</strong> first_name, last_name</li>
                        <li><strong>Optional:</strong> email, phone, address, city, state, zip_code, country, pipeline_stage, priority, notes</li>
                    </ul>
                    <p>Download a <a href="#" class="alert-link">sample CSV template</a>.</p>
                </div>
            '''),
            Div(
                Submit('submit', 'Import Contacts', css_class='btn btn-primary'),
                HTML('<a href="{% url \'contacts:person_list\' %}" class="btn btn-secondary ms-2">Cancel</a>'),
                css_class='mt-4'
            )
        )
