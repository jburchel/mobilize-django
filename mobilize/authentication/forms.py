from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML, Div
from crispy_forms.bootstrap import FormActions

from .models import User, UserContactSyncSettings


class UserContactSyncSettingsForm(forms.ModelForm):
    """Form for managing user contact sync preferences"""
    
    class Meta:
        model = UserContactSyncSettings
        fields = [
            'sync_preference', 
            'auto_sync_enabled', 
            'sync_frequency_hours'
        ]
        widgets = {
            'sync_frequency_hours': forms.NumberInput(attrs={'min': 1, 'max': 168}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Customize field labels and help text
        self.fields['sync_preference'].label = 'Contact Sync Mode'
        self.fields['sync_preference'].help_text = (
            'Choose how you want to sync your Google contacts with the CRM'
        )
        
        self.fields['auto_sync_enabled'].label = 'Enable Automatic Sync'
        self.fields['auto_sync_enabled'].help_text = (
            'Automatically sync contacts based on the frequency setting below'
        )
        
        self.fields['sync_frequency_hours'].label = 'Sync Frequency (Hours)'
        self.fields['sync_frequency_hours'].help_text = (
            'How often to automatically sync contacts (1-168 hours)'
        )
        
        # Set up crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        
        self.helper.layout = Layout(
            Fieldset(
                'Google Contacts Sync Settings',
                HTML('''
                    <div class="alert alert-info">
                        <h6><i class="fas fa-info-circle"></i> Sync Options Explained:</h6>
                        <ul class="mb-0">
                            <li><strong>Disabled:</strong> No contact synchronization</li>
                            <li><strong>CRM Only:</strong> Only sync contacts that already exist in the CRM</li>
                            <li><strong>All Contacts:</strong> Import all your Google contacts into the CRM</li>
                        </ul>
                    </div>
                '''),
                'sync_preference',
                'auto_sync_enabled',
                Div(
                    'sync_frequency_hours',
                    css_class='sync-frequency-field',
                    style='display: none;'  # Initially hidden
                ),
            ),
            FormActions(
                Submit('save', 'Save Settings', css_class='btn btn-primary'),
                HTML('<a href="{% url \'core:settings\' %}" class="btn btn-secondary">Cancel</a>'),
            )
        )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile information"""
    
    class Meta:
        model = User
        fields = [
            'first_name', 
            'last_name', 
            'email',
            'email_signature',
        ]
        widgets = {
            'email_signature': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Set up crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        
        self.helper.layout = Layout(
            Fieldset(
                'Personal Information',
                Row(
                    Column('first_name', css_class='col-md-6'),
                    Column('last_name', css_class='col-md-6'),
                ),
                'email',
                'email_signature',
            ),
            FormActions(
                Submit('save', 'Save Profile', css_class='btn btn-primary'),
                HTML('<a href="{% url \'core:profile\' %}" class="btn btn-secondary">Cancel</a>'),
            )
        )


class ContactSyncPreferenceForm(forms.Form):
    """Simple form for login-time contact sync preference selection"""
    
    sync_preference = forms.ChoiceField(
        choices=UserContactSyncSettings.SYNC_CHOICES,
        widget=forms.RadioSelect,
        initial='crm_only',
        label='How would you like to sync your Google contacts?'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'contact-sync-preference-form'
        
        self.helper.layout = Layout(
            HTML('''
                <div class="mb-3">
                    <h5>Contact Synchronization</h5>
                    <p class="text-muted">
                        We've detected you have a Google account. Choose how you'd like to handle 
                        contact synchronization between Google and your CRM:
                    </p>
                </div>
            '''),
            'sync_preference',
            HTML('''
                <div class="sync-explanation mt-3">
                    <div class="explanation-text" data-choice="disabled" style="display: none;">
                        <div class="alert alert-secondary">
                            <strong>No Sync:</strong> Your contacts will remain separate. 
                            You can change this setting later in your profile.
                        </div>
                    </div>
                    <div class="explanation-text" data-choice="crm_only" style="display: block;">
                        <div class="alert alert-info">
                            <strong>CRM Only:</strong> We'll only sync contact information for people 
                            and churches that already exist in your CRM. This keeps your Google contacts 
                            private while updating CRM records with Google contact data.
                        </div>
                    </div>
                    <div class="explanation-text" data-choice="all_contacts" style="display: none;">
                        <div class="alert alert-warning">
                            <strong>All Contacts:</strong> We'll import all your Google contacts into 
                            the CRM. This gives you a complete view but may import personal contacts 
                            you don't want in your work CRM.
                        </div>
                    </div>
                </div>
            '''),
            FormActions(
                Submit('save_and_continue', 'Save & Continue', css_class='btn btn-primary'),
                Submit('skip', 'Skip for Now', css_class='btn btn-secondary'),
            )
        )


class CreateUserForm(forms.ModelForm):
    """Form for creating new users manually (admin/office_admin only)"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Password must be at least 8 characters long'
    )
    password_confirm = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        label='Confirm Password',
        help_text='Enter the same password as above, for verification'
    )
    
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'username', 'role']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter first name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter last name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter username'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.created_by = kwargs.pop('created_by', None)
        super().__init__(*args, **kwargs)
        
        # Set email validation to require @crossoverglobal.net
        self.fields['email'].help_text = 'Must be a @crossoverglobal.net email address'
        
        # Filter role choices based on who is creating the user
        if self.created_by and self.created_by.role == 'office_admin':
            # Office admins can only create standard_user and limited_user
            self.fields['role'].choices = [
                ('standard_user', 'Standard User'),
                ('limited_user', 'Limited User'),
            ]
        elif self.created_by and self.created_by.role == 'super_admin':
            # Super admins can create any role
            self.fields['role'].choices = [
                ('standard_user', 'Standard User'),
                ('office_admin', 'Office Admin'),
                ('limited_user', 'Limited User'),
            ]
        else:
            # Default to standard user only
            self.fields['role'].choices = [
                ('standard_user', 'Standard User'),
            ]
        
        # Set up crispy forms
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'create-user-form'
        
        self.helper.layout = Layout(
            Fieldset(
                'User Information',
                Row(
                    Column('first_name', css_class='col-md-6'),
                    Column('last_name', css_class='col-md-6'),
                ),
                Row(
                    Column('email', css_class='col-md-6'),
                    Column('username', css_class='col-md-6'),
                ),
                'role',
            ),
            Fieldset(
                'Account Security',
                Row(
                    Column('password', css_class='col-md-6'),
                    Column('password_confirm', css_class='col-md-6'),
                ),
                HTML('''
                    <div class="alert alert-info">
                        <h6><i class="fas fa-info-circle"></i> Password Requirements:</h6>
                        <ul class="mb-0">
                            <li>At least 8 characters long</li>
                            <li>Recommend using a mix of letters, numbers, and symbols</li>
                            <li>User will be prompted to change password on first login</li>
                        </ul>
                    </div>
                '''),
            ),
            FormActions(
                Submit('create_user', 'Create User', css_class='btn btn-primary'),
                Submit('create_and_assign', 'Create & Assign to Office', css_class='btn btn-success'),
                HTML('<button type="button" class="btn btn-secondary" onclick="history.back()">Cancel</button>'),
            )
        )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not email.endswith('@crossoverglobal.net'):
            raise forms.ValidationError(
                'Email must be a @crossoverglobal.net address'
            )
        
        # Check if email already exists
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'A user with this email already exists'
            )
        
        return email
    
    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'A user with this username already exists'
            )
        return username
    
    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')
        
        if password and password_confirm:
            if password != password_confirm:
                raise forms.ValidationError(
                    'Passwords do not match'
                )
        
        if password and len(password) < 8:
            raise forms.ValidationError(
                'Password must be at least 8 characters long'
            )
        
        return cleaned_data
    
    def save(self, commit=True):
        user = super().save(commit=False)
        
        # Set password
        user.set_password(self.cleaned_data['password'])
        
        # Set is_active to True
        user.is_active = True
        
        if commit:
            user.save()
            
            # Create or get the Person record for this user
            user.get_or_create_person()
        
        return user