from django import forms
from django.core.validators import FileExtensionValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Div

from .models import Church
from mobilize.contacts.models import Contact


class ChurchForm(forms.ModelForm):
    """Form for creating and editing Church records."""
    
    # Contact fields that will be handled separately
    email = forms.EmailField(max_length=255, required=False)
    phone = forms.CharField(max_length=20, required=False)
    street_address = forms.CharField(max_length=255, required=False, label="Street Address")
    city = forms.CharField(max_length=255, required=False)
    state = forms.CharField(max_length=255, required=False)
    zip_code = forms.CharField(max_length=255, required=False, label="ZIP Code")
    country = forms.CharField(max_length=100, required=False)
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    
    # Pipeline and status with proper choices
    PIPELINE_CHOICES = [
        ('', '-- Select Pipeline Stage --'),
        ('promotion', 'Promotion'),
        ('information', 'Information'),
        ('invitation', 'Invitation'),
        ('confirmation', 'Confirmation'),
        ('automation', 'Automation'),
        ('en42', 'EN42'),
    ]
    
    PRIORITY_CHOICES = [
        ('', '-- Select Priority --'),
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    STATUS_CHOICES = [
        ('', '-- Select Status --'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
    ]
    
    pipeline_stage = forms.ChoiceField(choices=PIPELINE_CHOICES, required=False, label="Pipeline Stage")
    priority = forms.ChoiceField(choices=PRIORITY_CHOICES, required=False)
    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    
    class Meta:
        model = Church
        fields = [
            # Church-specific fields only
            'name', 'location', 'website', 'denomination', 'year_founded',
            'congregation_size', 'weekly_attendance',
            'service_times', 'facilities', 'ministries', 'primary_language', 'secondary_languages',
            # Pastor Information (removed pastor_name and main_contact_id)
            'senior_pastor_first_name', 'senior_pastor_last_name',
            'pastor_phone', 'pastor_email',
            'missions_pastor_first_name', 'missions_pastor_last_name',
            'mission_pastor_phone', 'mission_pastor_email',
            # Primary Contact Information  
            'primary_contact_first_name', 'primary_contact_last_name',
            'primary_contact_phone', 'primary_contact_email',
            # Church-specific fields (removed church_pipeline, made virtuous a toggle)
            'virtuous', 'info_given'
        ]
        widgets = {
            'info_given': forms.Textarea(attrs={'rows': 3}),
            'service_times': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., {"Sunday": "9am, 11am", "Wednesday": "7pm"}'}),
            'facilities': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., {"sanctuary_capacity": 500, "parking_spots": 100}'}),
            'ministries': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., ["Youth Group", "Food Pantry"]'}),
            'secondary_languages': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., ["Spanish", "Korean"]'}),
            'virtuous': forms.CheckboxInput(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Customize field labels for cleaner Leadership section
        self.fields['senior_pastor_first_name'].label = 'First Name'
        self.fields['senior_pastor_last_name'].label = 'Last Name'
        self.fields['pastor_phone'].label = 'Phone'
        self.fields['pastor_phone'].help_text = ''  # Remove help text
        self.fields['pastor_email'].label = 'Email'
        self.fields['pastor_email'].help_text = ''  # Remove help text
        self.fields['missions_pastor_first_name'].label = 'First Name'
        self.fields['missions_pastor_last_name'].label = 'Last Name'
        self.fields['mission_pastor_phone'].label = 'Phone'
        self.fields['mission_pastor_email'].label = 'Email'
        self.fields['primary_contact_first_name'].label = 'First Name'
        self.fields['primary_contact_last_name'].label = 'Last Name'
        self.fields['primary_contact_phone'].label = 'Phone'
        self.fields['primary_contact_email'].label = 'Email'
        
        # If we have an instance, populate Contact fields
        if self.instance and hasattr(self.instance, 'contact'):
            contact = self.instance.contact
            self.fields['email'].initial = contact.email
            self.fields['phone'].initial = contact.phone
            self.fields['street_address'].initial = contact.street_address
            self.fields['city'].initial = contact.city
            self.fields['state'].initial = contact.state
            self.fields['zip_code'].initial = contact.zip_code
            self.fields['country'].initial = contact.country
            self.fields['notes'].initial = contact.notes
            # Get pipeline stage through the pipeline system
            current_stage = contact.get_current_pipeline_stage()
            if current_stage:
                self.fields['pipeline_stage'].initial = current_stage.name
            self.fields['priority'].initial = contact.priority
            self.fields['status'].initial = contact.status
        
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-grid'
        
        self.helper.layout = Layout(
            # Basic Information Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-primary text-white"><h5 class="mb-0"><i class="fas fa-church me-2"></i>Basic Information</h5></div><div class="card-body">'),
                Row(
                    Column('name', css_class='col-md-6 mb-3'),
                    Column('denomination', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('location', css_class='col-md-6 mb-3'),
                    Column('website', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('year_founded', css_class='col-md-6 mb-3'),
                    Column('primary_language', css_class='col-md-6 mb-3'),
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
                HTML('</div></div>')
            ),
            
            # Leadership Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-warning text-dark"><h5 class="mb-0"><i class="fas fa-users me-2"></i>Leadership Information</h5></div><div class="card-body">'),
                HTML('<h6 class="border-bottom pb-2 mb-3">Senior Pastor</h6>'),
                Row(
                    Column('senior_pastor_first_name', css_class='col-md-6 mb-3'),
                    Column('senior_pastor_last_name', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('pastor_phone', css_class='col-md-6 mb-3'),
                    Column('pastor_email', css_class='col-md-6 mb-3'),
                ),
                HTML('<h6 class="border-bottom pb-2 mb-3 mt-4">Missions Pastor</h6>'),
                Row(
                    Column('missions_pastor_first_name', css_class='col-md-6 mb-3'),
                    Column('missions_pastor_last_name', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('mission_pastor_phone', css_class='col-md-6 mb-3'),
                    Column('mission_pastor_email', css_class='col-md-6 mb-3'),
                ),
                HTML('<h6 class="border-bottom pb-2 mb-3 mt-4">Primary Contact</h6>'),
                Row(
                    Column('primary_contact_first_name', css_class='col-md-6 mb-3'),
                    Column('primary_contact_last_name', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('primary_contact_phone', css_class='col-md-6 mb-3'),
                    Column('primary_contact_email', css_class='col-md-6 mb-3'),
                ),
                HTML('</div></div>')
            ),
            
            # Church Details Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-info text-white"><h5 class="mb-0"><i class="fas fa-info-circle me-2"></i>Church Details</h5></div><div class="card-body">'),
                Row(
                    Column('congregation_size', css_class='col-md-6 mb-3'),
                    Column('weekly_attendance', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('secondary_languages', css_class='col-md-6 mb-3'),
                    Column('service_times', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('facilities', css_class='col-md-6 mb-3'),
                    Column('ministries', css_class='col-md-6 mb-3'),
                ),
                HTML('</div></div>')
            ),
            
            # Status & Pipeline Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-secondary text-white"><h5 class="mb-0"><i class="fas fa-flag me-2"></i>Status & Pipeline</h5></div><div class="card-body">'),
                Row(
                    Column('pipeline_stage', css_class='col-md-6 mb-3'),
                    Column('priority', css_class='col-md-6 mb-3'),
                ),
                Row(
                    Column('status', css_class='col-md-6 mb-3'),
                    Column('virtuous', css_class='col-md-6 mb-3 d-flex align-items-center'),
                ),
                HTML('</div></div>')
            ),
            
            # Notes Section
            Div(
                HTML('<div class="card mb-4"><div class="card-header bg-dark text-white"><h5 class="mb-0"><i class="fas fa-sticky-note me-2"></i>Notes & Information</h5></div><div class="card-body">'),
                'notes',
                'info_given',
                HTML('</div></div>')
            ),
            
            # Action Buttons
            Div(
                Submit('submit', 'Save Church', css_class='btn btn-primary btn-lg me-3'),
                HTML('<a href="{% url \'churches:church_list\' %}" class="btn btn-secondary btn-lg">Cancel</a>'),
                css_class='text-center mt-4 mb-4'
            )
        )
    
    def save(self, commit=True, user=None, office=None):
        # Handle Contact creation/update
        if self.instance.pk:
            # Editing existing church
            contact = self.instance.contact
        else:
            # Creating new church
            contact = Contact(type='church')
            if user:
                contact.user = user
            if office:
                contact.office = office
        
        # Update contact fields
        contact.church_name = self.cleaned_data.get('name')
        contact.email = self.cleaned_data.get('email')
        contact.phone = self.cleaned_data.get('phone')
        contact.street_address = self.cleaned_data.get('street_address')
        contact.city = self.cleaned_data.get('city')
        contact.state = self.cleaned_data.get('state')
        contact.zip_code = self.cleaned_data.get('zip_code')
        contact.country = self.cleaned_data.get('country')
        contact.notes = self.cleaned_data.get('notes')
        contact.priority = self.cleaned_data.get('priority')
        contact.status = self.cleaned_data.get('status') or 'active'
        
        if commit:
            contact.save()
            if not self.instance.pk:
                # Only set contact for new instances
                self.instance.contact = contact
            church = super().save(commit=True)
            return church
        else:
            if not self.instance.pk:
                self.instance.contact = contact
            return super().save(commit=False)


# ChurchInteractionForm and ChurchContactForm have been removed as the related models don't exist in Supabase


class ImportChurchesForm(forms.Form):
    """Form for importing churches from a CSV file."""
    
    csv_file = forms.FileField(
        label='CSV File',
        help_text='Please upload a CSV file with church information.',
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
                        <li><strong>Required:</strong> church_name, city, state</li>
                        <li><strong>Optional:</strong> denomination, email, phone, street_address, zip_code, country, location, website,
                            congregation_size, weekly_attendance, year_founded, notes, church_pipeline, priority, assigned_to, source, referred_by</li>
                        <li><strong>Pastor Info (Optional):</strong> senior_pastor_name, senior_pastor_email, senior_pastor_phone</li>
                    </ul>
                    <p>Download a <a href="#" class="alert-link">sample CSV template</a>.</p>
                </div>
            '''),
            Div(
                Submit('submit', 'Import Churches', css_class='btn btn-primary'),
                HTML('<a href="{% url \'churches:church_list\' %}" class="btn btn-secondary ms-2">Cancel</a>'),
                css_class='mt-4'
            )
        )
