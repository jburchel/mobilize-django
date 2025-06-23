from django import forms
from django.utils import timezone
import pytz
from .models import Office


class OfficeForm(forms.ModelForm):
    """
    Enhanced Office form with improved field configurations and office settings.
    """
    
    # US States choices
    US_STATES = [
        ('', '-- Select State --'),
        ('AL', 'Alabama'), ('AK', 'Alaska'), ('AZ', 'Arizona'), ('AR', 'Arkansas'),
        ('CA', 'California'), ('CO', 'Colorado'), ('CT', 'Connecticut'), ('DE', 'Delaware'),
        ('FL', 'Florida'), ('GA', 'Georgia'), ('HI', 'Hawaii'), ('ID', 'Idaho'),
        ('IL', 'Illinois'), ('IN', 'Indiana'), ('IA', 'Iowa'), ('KS', 'Kansas'),
        ('KY', 'Kentucky'), ('LA', 'Louisiana'), ('ME', 'Maine'), ('MD', 'Maryland'),
        ('MA', 'Massachusetts'), ('MI', 'Michigan'), ('MN', 'Minnesota'), ('MS', 'Mississippi'),
        ('MO', 'Missouri'), ('MT', 'Montana'), ('NE', 'Nebraska'), ('NV', 'Nevada'),
        ('NH', 'New Hampshire'), ('NJ', 'New Jersey'), ('NM', 'New Mexico'), ('NY', 'New York'),
        ('NC', 'North Carolina'), ('ND', 'North Dakota'), ('OH', 'Ohio'), ('OK', 'Oklahoma'),
        ('OR', 'Oregon'), ('PA', 'Pennsylvania'), ('RI', 'Rhode Island'), ('SC', 'South Carolina'),
        ('SD', 'South Dakota'), ('TN', 'Tennessee'), ('TX', 'Texas'), ('UT', 'Utah'),
        ('VT', 'Vermont'), ('VA', 'Virginia'), ('WA', 'Washington'), ('WV', 'West Virginia'),
        ('WI', 'Wisconsin'), ('WY', 'Wyoming'),
    ]
    
    # Comprehensive world timezone choices
    TIMEZONE_CHOICES = [
        ('', '-- Select Timezone --'),
        # UTC
        ('UTC', 'UTC'),
        
        # North America
        ('America/New_York', 'Eastern Time (New York)'),
        ('America/Chicago', 'Central Time (Chicago)'),
        ('America/Denver', 'Mountain Time (Denver)'),
        ('America/Los_Angeles', 'Pacific Time (Los Angeles)'),
        ('America/Anchorage', 'Alaska Time (Anchorage)'),
        ('Pacific/Honolulu', 'Hawaii Time (Honolulu)'),
        ('America/Toronto', 'Eastern Time (Toronto)'),
        ('America/Vancouver', 'Pacific Time (Vancouver)'),
        ('America/Mexico_City', 'Central Time (Mexico City)'),
        ('America/Guatemala', 'Central Standard Time (Guatemala)'),
        ('America/Belize', 'Central Standard Time (Belize)'),
        
        # South America
        ('America/Sao_Paulo', 'Brasília Time (São Paulo)'),
        ('America/Argentina/Buenos_Aires', 'Argentina Time (Buenos Aires)'),
        ('America/Santiago', 'Chile Time (Santiago)'),
        ('America/Lima', 'Peru Time (Lima)'),
        ('America/Bogota', 'Colombia Time (Bogotá)'),
        ('America/Caracas', 'Venezuela Time (Caracas)'),
        
        # Europe
        ('Europe/London', 'Greenwich Mean Time (London)'),
        ('Europe/Dublin', 'Greenwich Mean Time (Dublin)'),
        ('Europe/Paris', 'Central European Time (Paris)'),
        ('Europe/Berlin', 'Central European Time (Berlin)'),
        ('Europe/Madrid', 'Central European Time (Madrid)'),
        ('Europe/Rome', 'Central European Time (Rome)'),
        ('Europe/Amsterdam', 'Central European Time (Amsterdam)'),
        ('Europe/Brussels', 'Central European Time (Brussels)'),
        ('Europe/Zurich', 'Central European Time (Zurich)'),
        ('Europe/Vienna', 'Central European Time (Vienna)'),
        ('Europe/Prague', 'Central European Time (Prague)'),
        ('Europe/Warsaw', 'Central European Time (Warsaw)'),
        ('Europe/Stockholm', 'Central European Time (Stockholm)'),
        ('Europe/Helsinki', 'Eastern European Time (Helsinki)'),
        ('Europe/Athens', 'Eastern European Time (Athens)'),
        ('Europe/Istanbul', 'Turkey Time (Istanbul)'),
        ('Europe/Moscow', 'Moscow Time (Moscow)'),
        
        # Africa
        ('Africa/Cairo', 'Eastern European Time (Cairo)'),
        ('Africa/Lagos', 'West Africa Time (Lagos)'),
        ('Africa/Nairobi', 'East Africa Time (Nairobi)'),
        ('Africa/Johannesburg', 'South Africa Time (Johannesburg)'),
        ('Africa/Casablanca', 'Western European Time (Casablanca)'),
        ('Africa/Accra', 'Greenwich Mean Time (Accra)'),
        ('Africa/Addis_Ababa', 'East Africa Time (Addis Ababa)'),
        
        # Asia
        ('Asia/Shanghai', 'China Standard Time (Shanghai)'),
        ('Asia/Beijing', 'China Standard Time (Beijing)'),
        ('Asia/Tokyo', 'Japan Standard Time (Tokyo)'),
        ('Asia/Seoul', 'Korea Standard Time (Seoul)'),
        ('Asia/Hong_Kong', 'Hong Kong Time (Hong Kong)'),
        ('Asia/Singapore', 'Singapore Time (Singapore)'),
        ('Asia/Bangkok', 'Indochina Time (Bangkok)'),
        ('Asia/Jakarta', 'Western Indonesia Time (Jakarta)'),
        ('Asia/Manila', 'Philippines Time (Manila)'),
        ('Asia/Kuala_Lumpur', 'Malaysia Time (Kuala Lumpur)'),
        ('Asia/Mumbai', 'India Standard Time (Mumbai)'),
        ('Asia/Kolkata', 'India Standard Time (Kolkata)'),
        ('Asia/Dhaka', 'Bangladesh Time (Dhaka)'),
        ('Asia/Karachi', 'Pakistan Time (Karachi)'),
        ('Asia/Dubai', 'Gulf Standard Time (Dubai)'),
        ('Asia/Riyadh', 'Arabia Standard Time (Riyadh)'),
        ('Asia/Tehran', 'Iran Time (Tehran)'),
        ('Asia/Jerusalem', 'Israel Time (Jerusalem)'),
        ('Asia/Beirut', 'Eastern European Time (Beirut)'),
        ('Asia/Damascus', 'Eastern European Time (Damascus)'),
        
        # Oceania
        ('Australia/Sydney', 'Australian Eastern Time (Sydney)'),
        ('Australia/Melbourne', 'Australian Eastern Time (Melbourne)'),
        ('Australia/Brisbane', 'Australian Eastern Time (Brisbane)'),
        ('Australia/Perth', 'Australian Western Time (Perth)'),
        ('Australia/Adelaide', 'Australian Central Time (Adelaide)'),
        ('Pacific/Auckland', 'New Zealand Time (Auckland)'),
        ('Pacific/Fiji', 'Fiji Time (Fiji)'),
        ('Pacific/Guam', 'Chamorro Time (Guam)'),
        
        # Central Asia
        ('Asia/Almaty', 'Almaty Time (Kazakhstan)'),
        ('Asia/Tashkent', 'Uzbekistan Time (Tashkent)'),
        ('Asia/Yekaterinburg', 'Yekaterinburg Time (Russia)'),
        ('Asia/Novosibirsk', 'Novosibirsk Time (Russia)'),
        ('Asia/Vladivostok', 'Vladivostok Time (Russia)'),
        
        # Additional important zones
        ('Pacific/Tahiti', 'Tahiti Time (French Polynesia)'),
        ('Atlantic/Azores', 'Azores Time (Portugal)'),
        ('Atlantic/Cape_Verde', 'Cape Verde Time'),
        ('Indian/Mauritius', 'Mauritius Time'),
        ('Indian/Maldives', 'Maldives Time'),
    ]
    
    # Override fields with custom widgets and configurations
    state = forms.ChoiceField(
        choices=US_STATES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    timezone_name = forms.ChoiceField(
        choices=TIMEZONE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='America/New_York'
    )
    
    address = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter street address',
            'rows': 2
        }),
        help_text='Street address for this office location'
    )
    
    # Office Settings as individual fields instead of JSON
    allow_cross_office_access = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Allow users from this office to access other offices'
    )
    
    default_pipeline = forms.ChoiceField(
        choices=[
            ('', '-- Select Default Pipeline --'),
            ('people', 'People Pipeline'),
            ('church', 'Church Pipeline'),
            ('custom', 'Custom Pipeline'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'}),
        help_text='Default pipeline for new contacts in this office'
    )
    
    enable_notifications = forms.BooleanField(
        required=False,
        initial=True,
        help_text='Enable email notifications for office users'
    )
    
    auto_assign_contacts = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Automatically assign new contacts to office users'
    )
    
    require_approval_for_deletions = forms.BooleanField(
        required=False,
        initial=True,
        help_text='Require admin approval before deleting contacts'
    )
    
    enable_advanced_reporting = forms.BooleanField(
        required=False,
        initial=False,
        help_text='Enable advanced reporting features for this office'
    )
    
    class Meta:
        model = Office
        fields = [
            'name', 'code', 'address', 'city', 'state', 'country', 
            'postal_code', 'phone', 'email', 'timezone_name', 'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter office name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., NYC, LA, CHI'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter city'}),
            'country': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter country', 'value': 'United States'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter postal code'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter phone number'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email address'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # If editing an existing office, populate settings fields from JSON
        if self.instance and self.instance.pk and self.instance.settings:
            settings = self.instance.settings
            self.fields['allow_cross_office_access'].initial = settings.get('allow_cross_office_access', False)
            self.fields['default_pipeline'].initial = settings.get('default_pipeline', '')
            self.fields['enable_notifications'].initial = settings.get('enable_notifications', True)
            self.fields['auto_assign_contacts'].initial = settings.get('auto_assign_contacts', False)
            self.fields['require_approval_for_deletions'].initial = settings.get('require_approval_for_deletions', True)
            self.fields['enable_advanced_reporting'].initial = settings.get('enable_advanced_reporting', False)
    
    def save(self, commit=True):
        """Override save to convert individual settings fields back to JSON."""
        instance = super().save(commit=False)
        
        # Build settings JSON from individual fields
        settings = {
            'allow_cross_office_access': self.cleaned_data.get('allow_cross_office_access', False),
            'default_pipeline': self.cleaned_data.get('default_pipeline', ''),
            'enable_notifications': self.cleaned_data.get('enable_notifications', True),
            'auto_assign_contacts': self.cleaned_data.get('auto_assign_contacts', False),
            'require_approval_for_deletions': self.cleaned_data.get('require_approval_for_deletions', True),
            'enable_advanced_reporting': self.cleaned_data.get('enable_advanced_reporting', False),
        }
        
        instance.settings = settings
        
        if commit:
            instance.save()
        
        return instance