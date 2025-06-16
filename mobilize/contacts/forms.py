from django import forms
from django.core.validators import FileExtensionValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Div

from .models import Person, Contact


class PersonForm(forms.ModelForm):
    """Form for creating and editing Person records."""
    
    # Contact fields that will be handled separately
    first_name = forms.CharField(max_length=255, required=False)
    last_name = forms.CharField(max_length=255, required=False)
    email = forms.EmailField(max_length=255, required=False)
    phone = forms.CharField(max_length=20, required=False)
    preferred_contact_method = forms.CharField(max_length=255, required=False)
    street_address = forms.CharField(max_length=255, required=False)
    city = forms.CharField(max_length=255, required=False)
    state = forms.CharField(max_length=255, required=False)
    zip_code = forms.CharField(max_length=255, required=False)
    country = forms.CharField(max_length=100, required=False)
    notes = forms.CharField(widget=forms.Textarea(attrs={'rows': 3}), required=False)
    pipeline_stage = forms.CharField(max_length=50, required=False)
    priority = forms.CharField(max_length=20, required=False)
    status = forms.CharField(max_length=20, required=False)
    tags = forms.CharField(widget=forms.Textarea(attrs={'rows': 2}), required=False)
    
    class Meta:
        model = Person
        fields = [
            # Person-specific fields only
            'title', 'preferred_name', 'birthday', 'anniversary', 'marital_status', 
            'spouse_first_name', 'spouse_last_name', 'home_country', 'languages', 
            'profession', 'organization', 'primary_church', 'church_role',
            'linkedin_url', 'facebook_url', 'twitter_url', 'instagram_url',
            'google_contact_id'
        ]
        widgets = {
            'languages': forms.Textarea(attrs={'rows': 2}),
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'anniversary': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
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
            self.fields['pipeline_stage'].initial = contact.pipeline_stage
            self.fields['priority'].initial = contact.priority
            self.fields['status'].initial = contact.status
            self.fields['tags'].initial = contact.tags
        
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-8'
        
        self.helper.layout = Layout(
            HTML('<h3 class="mb-4">Basic Information</h3>'),
            Row(
                Column('first_name', css_class='form-group col-md-6 mb-3'),
                Column('last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('email', css_class='form-group col-md-6 mb-3'),
                Column('phone', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'preferred_contact_method',
            
            HTML('<h3 class="mb-4 mt-4">Address</h3>'),
            'street_address',
            Row(
                Column('city', css_class='form-group col-md-4 mb-3'),
                Column('state', css_class='form-group col-md-4 mb-3'),
                Column('zip_code', css_class='form-group col-md-4 mb-3'),
                css_class='form-row'
            ),
            'country',
            
            HTML('<h3 class="mb-4 mt-4">Personal Details</h3>'),
            'title',
            'preferred_name',
            Row(
                Column('birthday', css_class='form-group col-md-6 mb-3'),
                Column('anniversary', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'marital_status',
            Row(
                Column('spouse_first_name', css_class='form-group col-md-6 mb-3'),
                Column('spouse_last_name', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'home_country',
            'languages',
            
            HTML('<h3 class="mb-4 mt-4">Professional Details</h3>'),
            'profession',
            'organization',
            
            HTML('<h3 class="mb-4 mt-4">Church Relationship</h3>'),
            'primary_church',
            'church_role',
            
            HTML('<h3 class="mb-4 mt-4">Pipeline and Status</h3>'),
            Row(
                Column('pipeline_stage', css_class='form-group col-md-6 mb-3'),
                Column('priority', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            'status',
            
            HTML('<h3 class="mb-4 mt-4">Notes</h3>'),
            'notes',
            'tags',
            
            HTML('<h3 class="mb-4 mt-4">Social Media</h3>'),
            'facebook_url',
            'twitter_url',
            'linkedin_url',
            'instagram_url',
            
            Div(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                HTML('<a href="{% url \'contacts:person_list\' %}" class="btn btn-secondary ms-2">Cancel</a>'),
                css_class='mt-4'
            )
        )
    
    def save(self, commit=True):
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
        contact.pipeline_stage = self.cleaned_data.get('pipeline_stage')
        contact.priority = self.cleaned_data.get('priority')
        contact.status = self.cleaned_data.get('status') or 'active'
        
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
            person = super().save(commit=True)
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
