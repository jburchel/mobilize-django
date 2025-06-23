from django import forms
from django.conf import settings
from django.utils import timezone
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, HTML, Div

from .models import Task # Import Task model
from mobilize.authentication.models import User
from mobilize.contacts.models import Person
from mobilize.churches.models import Church # Assuming Office is in admin_panel.models
from mobilize.admin_panel.models import Office


class TaskForm(forms.ModelForm):
    # Fields for recurrence rule definition
    is_recurring_template = forms.BooleanField(
        required=False, 
        label="Is this a recurring task template?",
        help_text="Check this if you want this task to repeat."
    )
    recurrence_frequency = forms.ChoiceField(
        choices=[('', '---------'), ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly')], # Simplified for now
        required=False,
        label="Frequency"
    )
    recurrence_interval = forms.IntegerField(min_value=1, initial=1, required=False, label="Repeat every")
    recurrence_weekdays = forms.MultipleChoiceField(
        choices=[(0, 'Mon'), (1, 'Tue'), (2, 'Wed'), (3, 'Thu'), (4, 'Fri'), (5, 'Sat'), (6, 'Sun')],
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="On (for weekly)"
    )
    recurrence_day_of_month = forms.IntegerField(min_value=1, max_value=31, required=False, label="Day of month (for monthly)")
    recurrence_end_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=False, 
        label="End recurrence on"
    )
    
    # Reminder option choices
    reminder_option = forms.ChoiceField(
        choices=[
            ('none', 'No reminder'),
            ('15_min_before', '15 minutes before'),
            ('30_min_before', '30 minutes before'),
            ('1_hour_before', '1 hour before'),
            ('2_hours_before', '2 hours before'),
            ('1_day_before', '1 day before'),
            ('2_days_before', '2 days before'),
            ('1_week_before', '1 week before'),
            ('on_due_time', 'At due time'),
            ('custom_on_due_date', 'Custom time on due date'),
        ],
        required=False,
        initial='none',
        label="Reminder"
    )

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'due_date', 'due_time', 
            'priority', 'status', 'category', 'type',
            'assigned_to', 'person', 'church', 'office',
            'reminder_option', 'reminder_time', 
            'google_calendar_sync_enabled', 
            # Recurrence fields from model are handled by custom form fields above
            # and processed in save() method:
            # 'is_recurring_template', 'recurring_pattern', 'recurrence_end_date'
            'completion_notes',
        ]
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'due_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'reminder_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
            # 'recurrence_end_date' is handled by custom form field widget
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Get the current user if passed
        super().__init__(*args, **kwargs)

        # Customize queryset for 'assigned_to' to users in the same office(s) or all if super_admin
        if user:
            if user.role == 'super_admin':
                self.fields['assigned_to'].queryset = User.objects.all()
            else:
                # Assuming UserOffice model links users to offices
                user_offices = user.useroffice_set.values_list('office_id', flat=True)
                self.fields['assigned_to'].queryset = User.objects.filter(
                    useroffice__office_id__in=user_offices
                ).distinct()

        # Populate recurrence form fields if instance exists and has recurrence
        if self.instance and self.instance.pk:
            self.fields['is_recurring_template'].initial = self.instance.is_recurring_template
            self.fields['recurrence_end_date'].initial = self.instance.recurrence_end_date
            if self.instance.recurring_pattern:
                self.fields['recurrence_frequency'].initial = self.instance.recurring_pattern.get('frequency')
                self.fields['recurrence_interval'].initial = self.instance.recurring_pattern.get('interval', 1)
                self.fields['recurrence_weekdays'].initial = self.instance.recurring_pattern.get('weekdays', [])
                self.fields['recurrence_day_of_month'].initial = self.instance.recurring_pattern.get('day_of_month')
        
        # Similarly, you might want to filter 'person', 'church', and 'office' based on user permissions
        # For now, keeping them as default ModelChoiceFields

        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.layout = Layout(
            Row(Column('title', css_class='form-group col-md-12 mb-3')),
            'description',
            Row(Column('due_date', css_class='form-group col-md-6 mb-3'), Column('due_time', css_class='form-group col-md-6 mb-3')),
            Row(Column('priority', css_class='form-group col-md-6 mb-3'), Column('status', css_class='form-group col-md-6 mb-3')),
            Row(Column('category', css_class='form-group col-md-6 mb-3'), Column('type', css_class='form-group col-md-6 mb-3')),
            Row(Column('assigned_to', css_class='form-group col-md-6 mb-3'), Column('office', css_class='form-group col-md-6 mb-3')),
            Row(
                Column('person', css_class='form-group col-md-6 mb-3'), 
                Column('church', css_class='form-group col-md-6 mb-3')
            ),
            Row(Column('reminder_option', css_class='form-group col-md-6 mb-3'), Column('reminder_time', css_class='form-group col-md-6 mb-3')),
            'google_calendar_sync_enabled',
            HTML("<hr><h4>Recurring Task Settings</h4>"),
            'is_recurring_template',
            Row(
                Column('recurrence_frequency', css_class='form-group col-md-6 mb-3'),
                Column('recurrence_interval', css_class='form-group col-md-6 mb-3'),
            ),
            # Conditional display for these fields can be handled with JavaScript later
            Div(
                'recurrence_weekdays', 
                css_class='form-group mb-3 recurrence-weekly-options' # Class for JS targeting
            ),
            Div(
                'recurrence_day_of_month', 
                css_class='form-group col-md-6 mb-3 recurrence-monthly-options' # Class for JS targeting
            ),
            'recurrence_end_date',
            'completion_notes', # Usually for non-template tasks, but can be here.
            Div(Submit('submit', 'Save Task', css_class='btn btn-primary mt-3'), css_class='form-group')
        )

    def clean(self):
        cleaned_data = super().clean()
        is_recurring = cleaned_data.get('is_recurring_template')
        frequency = cleaned_data.get('recurrence_frequency')

        if is_recurring and not frequency:
            self.add_error('recurrence_frequency', 'Frequency is required for recurring tasks.')
        
        if frequency == 'weekly' and not cleaned_data.get('recurrence_weekdays'):
            self.add_error('recurrence_weekdays', 'Please select at least one weekday for weekly recurrence.')
        
        if frequency == 'monthly' and not cleaned_data.get('recurrence_day_of_month'):
            self.add_error('recurrence_day_of_month', 'Day of month is required for monthly recurrence.')
            
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        instance.is_recurring_template = self.cleaned_data.get('is_recurring_template', False)
        instance.recurrence_end_date = self.cleaned_data.get('recurrence_end_date')

        if instance.is_recurring_template:
            instance.recurring_pattern = {
                "frequency": self.cleaned_data.get('recurrence_frequency'),
                "interval": self.cleaned_data.get('recurrence_interval', 1),
                "weekdays": [int(wd) for wd in self.cleaned_data.get('recurrence_weekdays', [])] if self.cleaned_data.get('recurrence_frequency') == 'weekly' else None,
                "day_of_month": self.cleaned_data.get('recurrence_day_of_month') if self.cleaned_data.get('recurrence_frequency') == 'monthly' else None,
            }
            
            if instance.due_date: # due_date is set on the instance by super().save(commit=False) from cleaned_data
                due_time_value = self.cleaned_data.get('due_time')
                if due_time_value:
                    # If due_time is a string (from TimeInput widget), convert it to time object
                    if isinstance(due_time_value, str):
                        from datetime import datetime
                        time_component = datetime.strptime(due_time_value, '%H:%M').time()
                    else:
                        time_component = due_time_value
                else:
                    time_component = timezone.datetime.min.time()
                naive_datetime = timezone.datetime.combine(instance.due_date, time_component)
                instance.next_occurrence_date = timezone.make_aware(naive_datetime)
            else:
                # If no due_date (start date) for the template, next_occurrence_date is None.
                # Generation logic will skip this template until a due_date is set.
                instance.next_occurrence_date = None
        else: 
            # If not a recurring template, clear all recurrence fields
            instance.recurring_pattern = None
            instance.next_occurrence_date = None
            instance.is_recurring_template = False # Explicitly set to False
            instance.recurrence_end_date = None # Clear end date if not recurring

        if commit:
            instance.save()
            self.save_m2m() # Important if there were any m2m fields
        return instance


class TaskFilterForm(forms.Form):
    """Form for filtering tasks in the task list view."""
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Task.STATUS_CHOICES, # Use model choices directly
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    priority = forms.ChoiceField(
        choices=[('', 'All Priorities')] + Task.PRIORITY_CHOICES, # Use model choices directly
        required=False,
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    assigned_to = forms.ModelChoiceField(
        queryset=User.objects.all(), # Will filter in __init__
        required=False,
        empty_label="All Users",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    office = forms.ModelChoiceField(
        queryset=Office.objects.all(), # Will filter in __init__ if needed
        required=False,
        empty_label="All Offices",
        widget=forms.Select(attrs={'class': 'form-select form-select-sm'})
    )
    due_date_start = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )
    due_date_end = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control form-control-sm'})
    )
    search = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Search title or description', 'class': 'form-control form-control-sm'})
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None) # Get the current user if passed
        super().__init__(*args, **kwargs)

        # Customize queryset for 'assigned_to' and 'office' based on user permissions
        if user:
            if user.role == 'super_admin':
                self.fields['assigned_to'].queryset = User.objects.all()
                self.fields['office'].queryset = Office.objects.all()
            else:
                # Assuming UserOffice model links users to offices
                user_offices = user.useroffice_set.values_list('office_id', flat=True)
                self.fields['assigned_to'].queryset = User.objects.filter(
                    useroffice__office_id__in=user_offices
                ).distinct()
                self.fields['office'].queryset = Office.objects.filter(id__in=user_offices)

        self.helper = FormHelper()
        self.helper.form_method = 'get' # Filtering is typically done with GET
        self.helper.layout = Layout(
            Row(
                Column('status', css_class='form-group col-md-3 mb-2'),
                Column('priority', css_class='form-group col-md-3 mb-2'),
                Column('assigned_to', css_class='form-group col-md-3 mb-2'),
                Column('office', css_class='form-group col-md-3 mb-2'),
            ),
            Row(
                Column('due_date_start', css_class='form-group col-md-3 mb-2'),
                Column('due_date_end', css_class='form-group col-md-3 mb-2'),
                Column('search', css_class='form-group col-md-6 mb-2'),
            ),
            Div(Submit('filter', 'Apply Filters', css_class='btn btn-primary btn-sm'), css_class='form-group text-end')
        )