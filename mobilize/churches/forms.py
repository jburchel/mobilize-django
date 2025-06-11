from django import forms
from django.core.validators import FileExtensionValidator
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Div

from .models import Church

# ChurchInteraction and ChurchContact models have been removed as they don't exist in Supabase
# Person import removed as it's no longer needed after removing ChurchContactForm


class ChurchForm(forms.ModelForm):
    """Form for creating and editing Church records."""
    
    class Meta:
        model = Church
        fields = [
            'name', # Renamed from church_name
            # Website
            'website',
            # Church-specific fields
            'denomination', 'year_founded',
            # Size Information
            'congregation_size', 'weekly_attendance',
            # New JSON fields
            'service_times', 'facilities', 'ministries', 'primary_language', 'secondary_languages',
            # Senior Pastor Information
            'pastor_name', # Renamed from senior_pastor_name
            'senior_pastor_first_name', 'senior_pastor_last_name',
            'pastor_phone', # Renamed from senior_pastor_phone
            'pastor_email', # Renamed from senior_pastor_email
            # Missions Pastor Information
            'missions_pastor_first_name', 'missions_pastor_last_name',
            'missions_pastor_phone', # Was mission_pastor_phone
            'missions_pastor_email', # Was mission_pastor_email
            # Primary Contact Information
            'primary_contact_first_name', 'primary_contact_last_name',
            'primary_contact_phone', 'primary_contact_email',
            'main_contact_id',
            # Pipeline and Status
            'virtuous', 'date_closed', # church_pipeline, priority, assigned_to are on Contact model
            # Source information
            'source', 'referred_by',
            # Church-specific notes and information
            'info_given', 'reason_closed',
            # owner_id and office_id are on Contact model
        ]
        widgets = {
            'info_given': forms.Textarea(attrs={'rows': 3}),
            'reason_closed': forms.Textarea(attrs={'rows': 3}),
            'date_closed': forms.DateInput(attrs={'type': 'date'}),
            'service_times': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., {"Sunday": "9am, 11am", "Wednesday": "7pm"}'}),
            'facilities': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., {"sanctuary_capacity": 500, "parking_spots": 100}'}),
            'ministries': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., ["Youth Group", "Food Pantry"]'}),
            'secondary_languages': forms.Textarea(attrs={'rows': 2, 'placeholder': 'e.g., ["Spanish", "Korean"]'}),
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
            'name',
            'denomination',
            Row(
                Column('website', css_class='form-group col-md-6 mb-3'),
                Column('year_founded', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
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
                Column('missions_pastor_phone', css_class='form-group col-md-6 mb-3'),
                Column('missions_pastor_email', css_class='form-group col-md-6 mb-3'),
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
                # church_pipeline, priority, assigned_to are on Contact model
                Column('virtuous', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            Row(
                Column('date_closed', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            HTML('<h3 class="mb-4 mt-4">Source Information</h3>'),
            Row(
                Column('source', css_class='form-group col-md-6 mb-3'),
                Column('referred_by', css_class='form-group col-md-6 mb-3'),
                css_class='form-row'
            ),
            HTML('<h3 class="mb-4 mt-4">Additional Information</h3>'),
            # notes, owner_id, office_id are on Contact model
            'info_given',
            'reason_closed',
            Div(
                Submit('submit', 'Save', css_class='btn btn-primary'),
                HTML('<a href="{% url \'churches:church_list\' %}" class="btn btn-secondary ms-2">Cancel</a>'),
                css_class='mt-4'
            )
        )


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
