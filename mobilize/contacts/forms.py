from django import forms
from django.core.validators import FileExtensionValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Div

from .models import Person


class PersonForm(forms.ModelForm):
    """Form for creating and editing Person records."""
    
    class Meta:
        model = Person
        fields = [
            # Contact fields (inherited)
            'first_name', 'last_name', 'email', 'phone', 'preferred_contact_method',
            'street_address', 'city', 'state', 'zip_code', 'country', 'notes',
            # Person-specific fields
            'birthday', 'anniversary', 'marital_status', 'spouse_first_name', 'spouse_last_name',
            'home_country', 'languages', 'occupation', 'employer', 'skills', 'interests',
            'church_id', 'church_role', 'is_primary_contact', 'pipeline_stage',
            'people_pipeline', 'priority', 'status', 'last_contact', 'next_contact',
            'date_closed', 'info_given', 'desired_service', 'reason_closed', 'tags',
            'assigned_to', 'source', 'referred_by', 'website', 'facebook', 'twitter',
            'linkedin', 'instagram', 'virtuous'
        ]
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
            'tags': forms.Textarea(attrs={'rows': 2}),
            'skills': forms.Textarea(attrs={'rows': 2}),
            'interests': forms.Textarea(attrs={'rows': 2}),
            'info_given': forms.Textarea(attrs={'rows': 3}),
            'desired_service': forms.Textarea(attrs={'rows': 3}),
            'reason_closed': forms.Textarea(attrs={'rows': 3}),
            'languages': forms.Textarea(attrs={'rows': 2}),
            'birthday': forms.DateInput(attrs={'type': 'date'}),
            'anniversary': forms.DateInput(attrs={'type': 'date'}),
            'last_contact': forms.DateInput(attrs={'type': 'date'}),
            'next_contact': forms.DateInput(attrs={'type': 'date'}),
            'date_closed': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
            'occupation',
            'employer',
            'skills',
            'interests',
            
            HTML('<h3 class="mb-4 mt-4">Church Relationship</h3>'),
            'church_id',
            'church_role',
            'is_primary_contact',
            
            HTML('<h3 class="mb-4 mt-4">Pipeline and Status</h3>'),
            Row(
                Column('pipeline_stage', css_class='form-group col-md-6 mb-3'),
                Column('people_pipeline', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('priority', css_class='form-group col-md-6 mb-3'),
                Column('status', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            
            HTML('<h3 class="mb-4 mt-4">Dates and Tracking</h3>'),
            Row(
                Column('last_contact', css_class='form-group col-md-4 mb-3'),
                Column('next_contact', css_class='form-group col-md-4 mb-3'),
                Column('date_closed', css_class='form-group col-md-4 mb-3'),
                css_class='form-row'
            ),
            
            HTML('<h3 class="mb-4 mt-4">Notes and Metadata</h3>'),
            'notes',
            'info_given',
            'desired_service',
            'reason_closed',
            'tags',
            
            HTML('<h3 class="mb-4 mt-4">Assignment</h3>'),
            'assigned_to',
            
            HTML('<h3 class="mb-4 mt-4">Source Information</h3>'),
            'source',
            'referred_by',
            
            HTML('<h3 class="mb-4 mt-4">Social Media</h3>'),
            'website',
            'facebook',
            'twitter',
            'linkedin',
            'instagram',
            
            HTML('<h3 class="mb-4 mt-4">Integration</h3>'),
            'virtuous',
            
            Div(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                HTML('<a href="{% url \'contacts:person_list\' %}" class="btn btn-secondary ms-2">Cancel</a>'),
                css_class='mt-4'
            )
        )



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
