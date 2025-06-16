from django import forms
from django.core.validators import FileExtensionValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Div

from .models import Church
from mobilize.contacts.models import Contact


class ChurchForm(forms.ModelForm):
    """Form for creating and editing Church records."""
    
    # Contact fields that will be handled separately
    church_name = forms.CharField(max_length=255, required=False, label="Church Name")
    email = forms.EmailField(max_length=255, required=False)
    phone = forms.CharField(max_length=20, required=False)
    street_address = forms.CharField(max_length=255, required=False)
    city = forms.CharField(max_length=255, required=False)
    state = forms.CharField(max_length=255, required=False)
    zip_code = forms.CharField(max_length=255, required=False)
    country = forms.CharField(max_length=100, required=False)
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    pipeline_stage = forms.CharField(max_length=50, required=False)
    priority = forms.CharField(max_length=20, required=False)
    status = forms.CharField(max_length=20, required=False)
    
    class Meta:
        model = Church
        fields = [
            # Church-specific fields only
            'name', 'location', 'website', 'denomination', 'year_founded',
            'congregation_size', 'weekly_attendance',
            'service_times', 'facilities', 'ministries', 'primary_language', 'secondary_languages',
            # Pastor Information
            'pastor_name', 'senior_pastor_first_name', 'senior_pastor_last_name',
            'pastor_phone', 'pastor_email',
            'missions_pastor_first_name', 'missions_pastor_last_name',
            'mission_pastor_phone', 'mission_pastor_email',
            # Primary Contact Information
            'primary_contact_first_name', 'primary_contact_last_name',
            'primary_contact_phone', 'primary_contact_email',
            'main_contact_id',
            # Church-specific fields
            'church_pipeline', 'virtuous', 'info_given'
        ]
        widgets = {
            'info_given': forms.Textarea(attrs={'rows': 3}),
            'service_times': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., {"Sunday": "9am, 11am", "Wednesday": "7pm"}'}),
            'facilities': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., {"sanctuary_capacity": 500, "parking_spots": 100}'}),
            'ministries': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., ["Youth Group", "Food Pantry"]'}),
            'secondary_languages': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., ["Spanish", "Korean"]'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If we have an instance, populate Contact fields
        if self.instance and hasattr(self.instance, 'contact'):
            contact = self.instance.contact
            self.fields['church_name'].initial = contact.church_name
            self.fields['email'].initial = contact.email
            self.fields['phone'].initial = contact.phone
            self.fields['street_address'].initial = contact.street_address
            self.fields['city'].initial = contact.city
            self.fields['state'].initial = contact.state
            self.fields['zip_code'].initial = contact.zip_code
            self.fields['country'].initial = contact.country
            self.fields['notes'].initial = contact.notes
            self.fields['pipeline_stage'].initial = contact.pipeline_stage
            self.fields['priority'].initial = contact.priority
            self.fields['status'].initial = contact.status
        
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        
        self.helper.layout = Layout(
            HTML('<h3 class="mb-4">Basic Information</h3>'),
            'church_name',
            'name',
            Row(
                Column('email', css_class='form-group col-md-6 mb-3'),
                Column('phone', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'location',
            'denomination',
            Row(
                Column('website', css_class='form-group col-md-6 mb-3'),
                Column('year_founded', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            
            HTML('<h3 class="mb-4 mt-4">Address</h3>'),
            'street_address',
            Row(
                Column('city', css_class='form-group col-md-4 mb-3'),
                Column('state', css_class='form-group col-md-4 mb-3'),
                Column('zip_code', css_class='form-group col-md-4 mb-3'),
                css_class='form-row'
            ),
            'country',
            
            HTML('<h3 class="mb-4 mt-4">Language & Services</h3>'),
            Row(
                Column('primary_language', css_class='form-group col-md-6 mb-3'),
                Column('secondary_languages', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),

            HTML('<h3 class="mb-4 mt-4">Church Size & Services</h3>'),
            Row(
                Column('congregation_size', css_class='form-group col-md-6 mb-3'),
                Column('weekly_attendance', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'service_times',
            Row(
                Column('facilities', css_class='form-group col-md-6 mb-3'),
                Column('ministries', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            HTML('<h3 class="mb-4 mt-4">Senior Pastor Information</h3>'),
            'pastor_name',
            Row(
                Column('senior_pastor_first_name', css_class='form-group col-md-6 mb-3'),
                Column('senior_pastor_last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('pastor_phone', css_class='form-group col-md-6 mb-3'),
                Column('pastor_email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            HTML('<h3 class="mb-4 mt-4">Missions Pastor Information</h3>'),
            Row(
                Column('missions_pastor_first_name', css_class='form-group col-md-6 mb-3'),
                Column('missions_pastor_last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('mission_pastor_phone', css_class='form-group col-md-6 mb-3'),
                Column('mission_pastor_email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            HTML('<h3 class="mb-4 mt-4">Primary Contact Information</h3>'),
            Row(
                Column('primary_contact_first_name', css_class='form-group col-md-6 mb-3'),
                Column('primary_contact_last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('primary_contact_phone', css_class='form-group col-md-6 mb-3'),
                Column('primary_contact_email', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'main_contact_id',
            HTML('<h3 class="mb-4 mt-4">Pipeline & Status</h3>'),
            Row(
                Column('pipeline_stage', css_class='form-group col-md-6 mb-3'),
                Column('priority', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('church_pipeline', css_class='form-group col-md-6 mb-3'),
                Column('status', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'virtuous',
            
            HTML('<h3 class="mb-4 mt-4">Notes & Information</h3>'),
            'notes',
            'info_given',
            Div(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                HTML('<a href="{% url \'churches:church_list\' %}" class="btn btn-secondary ms-2">Cancel</a>'),
                css_class='mt-4'
            )
        )
    
    def save(self, commit=True):
        # Handle Contact creation/update
        if self.instance.pk:
            # Editing existing church
            contact = self.instance.contact
        else:
            # Creating new church
            contact = Contact(type='church')
        
        # Update contact fields
        contact.church_name = self.cleaned_data.get('church_name')
        contact.email = self.cleaned_data.get('email')
        contact.phone = self.cleaned_data.get('phone')
        contact.street_address = self.cleaned_data.get('street_address')
        contact.city = self.cleaned_data.get('city')
        contact.state = self.cleaned_data.get('state')
        contact.zip_code = self.cleaned_data.get('zip_code')
        contact.country = self.cleaned_data.get('country')
        contact.notes = self.cleaned_data.get('notes')
        contact.pipeline_stage = self.cleaned_data.get('pipeline_stage')
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
