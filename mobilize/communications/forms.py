from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, HTML
from crispy_forms.bootstrap import FormActions

from .models import EmailTemplate, EmailSignature, Communication, EmailAttachment


class EmailTemplateForm(forms.ModelForm):
    """Form for creating and editing email templates"""
    
    class Meta:
        model = EmailTemplate
        fields = ['name', 'subject', 'body', 'is_html', 'category', 'is_active']
        widgets = {
            'body': forms.Textarea(attrs={'rows': 10}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-2'
        self.helper.field_class = 'col-lg-10'
        
        self.helper.layout = Layout(
            Fieldset(
                'Template Information',
                'name',
                'category',
                'is_active',
            ),
            Fieldset(
                'Email Content',
                'subject',
                'body',
                'is_html',
            ),
            FormActions(
                Submit('save', 'Save Template', css_class='btn btn-primary'),
                HTML('<a href="{% url \'communications:email_template_list\' %}" class="btn btn-secondary">Cancel</a>'),
            )
        )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user and not instance.pk:  # Only set created_by on new instances
            instance.created_by = self.user
        if commit:
            instance.save()
        return instance


class EmailSignatureForm(forms.ModelForm):
    """Form for creating and editing email signatures"""
    
    class Meta:
        model = EmailSignature
        fields = ['name', 'content', 'is_html', 'is_default']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 5}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('is_default', css_class='col-md-6'),
                css_class='form-row'
            ),
            'content',
            HTML('<small class="form-text text-muted">Company logo will be automatically added to all email signatures.</small>'),
            Row(
                Column('is_html', css_class='col-md-6'),
                css_class='form-row'
            ),
            FormActions(
                Submit('save', 'Save Signature', css_class='btn btn-primary'),
                HTML('<a href="{% url \'communications:email_signature_list\' %}" class="btn btn-secondary">Cancel</a>'),
            )
        )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.user:
            instance.user = self.user
        if commit:
            instance.save()
        return instance


class CommunicationForm(forms.ModelForm):
    """Form for creating and editing communications"""
    
    class Meta:
        model = Communication
        fields = [
            'type', 'message', 'subject', 'direction', 'date', 'date_sent',
            'person', 'church', 'gmail_message_id', 'gmail_thread_id',
            'email_status', 'attachments', 'sender', 'owner_id',
            'office', 'google_calendar_event_id', 'google_meet_link'
        ]
        widgets = {
            'message': forms.Textarea(attrs={'rows': 4, 'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'date_sent': forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
            'type': forms.Select(attrs={'class': 'form-control'}),
            'direction': forms.Select(attrs={'class': 'form-control'}),
            'person': forms.Select(attrs={'class': 'form-control'}),
            'church': forms.Select(attrs={'class': 'form-control'}),
            'office': forms.Select(attrs={'class': 'form-control'}),
            'gmail_message_id': forms.TextInput(attrs={'class': 'form-control'}),
            'gmail_thread_id': forms.TextInput(attrs={'class': 'form-control'}),
            'email_status': forms.TextInput(attrs={'class': 'form-control'}),
            'attachments': forms.TextInput(attrs={'class': 'form-control'}),
            'sender': forms.TextInput(attrs={'class': 'form-control'}),
            'owner_id': forms.NumberInput(attrs={'class': 'form-control'}),
            'google_calendar_event_id': forms.TextInput(attrs={'class': 'form-control'}),
            'google_meet_link': forms.URLInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Set choices for type and direction fields
        if hasattr(Communication, 'TYPE_CHOICES'):
            self.fields['type'].widget = forms.Select(choices=Communication.TYPE_CHOICES, attrs={'class': 'form-control'})
        
        if hasattr(Communication, 'DIRECTION_CHOICES'):
            self.fields['direction'].widget = forms.Select(choices=Communication.DIRECTION_CHOICES, attrs={'class': 'form-control'})
        
        # Set up form helper
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        
        # Use the actual model fields that exist
        self.helper.layout = Layout(
            Fieldset(
                'Communication Details',
                Row(
                    Column('type', css_class='col-md-6'),
                    Column('direction', css_class='col-md-6'),
                    css_class='form-row'
                ),
                Row(
                    Column('date', css_class='col-md-6'),
                    Column('date_sent', css_class='col-md-6'),
                    css_class='form-row'
                ),
                'subject',
                'message',
            ),
            Fieldset(
                'Related Records',
                Row(
                    Column('person', css_class='col-md-6'),
                    Column('church', css_class='col-md-6'),
                    css_class='form-row'
                ),
                'office',
            ),
            Fieldset(
                'Email & Integration Details',
                Row(
                    Column('sender', css_class='col-md-6'),
                    Column('email_status', css_class='col-md-6'),
                    css_class='form-row'
                ),
                Row(
                    Column('gmail_message_id', css_class='col-md-6'),
                    Column('gmail_thread_id', css_class='col-md-6'),
                    css_class='form-row'
                ),
                Row(
                    Column('attachments', css_class='col-md-6'),
                    Column('owner_id', css_class='col-md-6'),
                    css_class='form-row'
                ),
                Row(
                    Column('google_calendar_event_id', css_class='col-md-6'),
                    Column('google_meet_link', css_class='col-md-6'),
                    css_class='form-row'
                ),
            ),
            FormActions(
                Submit('save', 'Save Communication', css_class='btn btn-primary'),
                HTML('<a href="{% url \'communications:communication_list\' %}" class="btn btn-secondary">Cancel</a>'),
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure at least one contact (person or church) is specified for new communications
        person = cleaned_data.get('person')
        church = cleaned_data.get('church')
        
        if not person and not church:
            # For imported communications, this might be acceptable, so we'll make it a warning rather than an error
            pass
        
        # Validate date fields
        date = cleaned_data.get('date')
        date_sent = cleaned_data.get('date_sent')
        
        try:
            if date_sent and not date:
                # If date_sent is provided but date is not, use date_sent as the date
                cleaned_data['date'] = date_sent.date()
        except (AttributeError, ValueError):
            # Handle cases where date_sent might not be a valid datetime
            pass
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Only set user on new instances
        if self.user and not instance.pk:
            instance.user = self.user
        
        # Set default values for required fields if they're missing (for imported data)
        if not instance.type:
            instance.type = 'Email'  # Default type for imported communications
            
        if not instance.direction:
            instance.direction = 'Outgoing'  # Use valid choice from DIRECTION_CHOICES
            
        try:
            if commit:
                instance.save()
        except Exception as e:
            # Log the error but don't crash
            print(f"Error saving communication: {e}")
            raise
            
        return instance


class EmailAttachmentForm(forms.ModelForm):
    """Form for uploading email attachments"""
    
    class Meta:
        model = EmailAttachment
        fields = ['file']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.form_class = 'form-inline'
        
        self.helper.layout = Layout(
            'file',
            Submit('upload', 'Upload', css_class='btn btn-primary ml-2')
        )
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set filename and content_type based on the uploaded file
        if instance.file:
            instance.filename = instance.file.name
            instance.content_type = instance.file.content_type
            instance.size = instance.file.size
            
        if commit:
            instance.save()
        return instance


class ComposeEmailForm(forms.Form):
    """Form for composing and sending emails via Gmail"""
    
    recipients = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 2}), 
        help_text="Separate multiple email addresses with commas"
    )
    cc = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'rows': 1}),
        help_text="Carbon copy recipients (optional)"
    )
    bcc = forms.CharField(
        required=False, 
        widget=forms.Textarea(attrs={'rows': 1}),
        help_text="Blind carbon copy recipients (optional)"
    )
    subject = forms.CharField()
    template = forms.ModelChoiceField(
        queryset=EmailTemplate.objects.filter(is_active=True),
        required=False,
        help_text="Select a template to use as a starting point"
    )
    signature = forms.ModelChoiceField(
        queryset=EmailSignature.objects.none(),  # Will be set in __init__
        required=False
    )
    body = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 10}),
        help_text="Email content"
    )
    is_html = forms.BooleanField(
        required=False, 
        initial=True,
        help_text="Send as HTML email"
    )
    related_person_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    related_church_id = forms.IntegerField(required=False, widget=forms.HiddenInput())
    attachments = forms.FileField(
        widget=forms.ClearableFileInput(attrs={'multiple': True}), 
        required=False,
        help_text="Attach files (optional)"
    )
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Filter signatures by user
        if self.user:
            self.fields['signature'].queryset = EmailSignature.objects.filter(user=self.user)
            # Set default signature if available
            default_sig = EmailSignature.objects.filter(user=self.user, is_default=True).first()
            if default_sig:
                self.fields['signature'].initial = default_sig.pk
        
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        
        self.helper.layout = Layout(
            Fieldset(
                'Recipients',
                'recipients',
                Row(
                    Column('cc', css_class='col-md-6'),
                    Column('bcc', css_class='col-md-6'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Email Content',
                'subject',
                Row(
                    Column('template', css_class='col-md-6'),
                    Column('signature', css_class='col-md-6'),
                    css_class='form-row'
                ),
                'body',
                Row(
                    Column('is_html', css_class='col-md-6'),
                    Column('attachments', css_class='col-md-6'),
                    css_class='form-row'
                ),
                'related_person_id',
                'related_church_id',
            ),
            FormActions(
                Submit('send', 'Send Email', css_class='btn btn-primary'),
                Submit('save_draft', 'Save Draft', css_class='btn btn-secondary'),
                HTML('<a href="{% url \'communications:communication_list\' %}" class="btn btn-light">Cancel</a>'),
            )
        )
