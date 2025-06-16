from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from mobilize.contacts.models import Person # Contact model is not directly used here, Person and Church are.
from mobilize.churches.models import Church
from mobilize.admin_panel.models import Office


class Task(models.Model):
    """
    Task model for storing task information.
    
    This model represents tasks in the CRM system.
    Matches the 'tasks' table in the Supabase database.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    # Basic Information
    # id = models.AutoField(primary_key=True) # Django adds this automatically
    title = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    
    # Dates and Times
    due_date = models.DateField(blank=True, null=True)
    due_time = models.CharField(max_length=255, blank=True, null=True)
    due_time_details = models.TextField(blank=True, null=True)
    reminder_time = models.CharField(max_length=255, blank=True, null=True)
    reminder_option = models.CharField(max_length=255, default='none', blank=True, null=True)
    reminder_sent = models.BooleanField(default=False, blank=True, null=True)
    
    # Status and Priority
    priority = models.CharField(max_length=50, choices=PRIORITY_CHOICES, default='medium', blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending', blank=True, null=True)
    category = models.CharField(max_length=255, blank=True, null=True)
    type = models.CharField(max_length=50, default='general') # Reduced max_length
    
    # Related Entities
    person = models.ForeignKey(Person, on_delete=models.SET_NULL, blank=True, null=True, related_name='person_tasks', db_column='person_id')
    church = models.ForeignKey(Church, on_delete=models.SET_NULL, blank=True, null=True, related_name='church_tasks', db_column='church_id')
    # The 'contact' field in Supabase schema seems to be a generic link.
    # In Django, it's better to link specifically to Person or Church.
    # If a task can be linked to EITHER a Person OR a Church (but not both simultaneously),
    # and also sometimes to neither, then having separate person and church FKs is fine.
    # If it's meant to link to a generic Contact (which then resolves to Person/Church),
    contact = models.ForeignKey('contacts.Contact', on_delete=models.SET_NULL, blank=True, null=True, related_name='contact_tasks', db_column='contact_id')
    
    # Assignment and Ownership
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL, # Or models.PROTECT if a task should not exist without a creator
        related_name='created_tasks',
        null=True, blank=True # Assuming created_by can be null if user is deleted or task is system-generated
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='assigned_tasks',
        null=True, blank=True # A task might not be assigned initially
    )
    office = models.ForeignKey(Office, on_delete=models.SET_NULL, blank=True, null=True, related_name='tasks', db_column='office_id')
    
    # Completion Information
    completed_at = models.DateTimeField(blank=True, null=True)
    completed_date = models.DateTimeField(blank=True, null=True)
    completion_notes = models.TextField(blank=True, null=True)
    
    # Google Calendar Integration
    google_calendar_event_id = models.CharField(max_length=255, blank=True, null=True)
    google_calendar_sync_enabled = models.BooleanField(blank=True, null=True)
    last_synced_at = models.DateTimeField(blank=True, null=True)
    
    # Recurring Task Fields
    # recurring_pattern is already defined in mobilize-prompt-django.md and supabase_schema.md
    # Example: {"frequency": "weekly", "interval": 1, "weekdays": [0, 2], "end_date": "YYYY-MM-DD"}
    # 0=Monday, 1=Tuesday, ..., 6=Sunday
    recurring_pattern = models.JSONField(blank=True, null=True, help_text="Defines the recurrence rule, e.g., weekly, monthly.")
    is_recurring_template = models.BooleanField(default=False, help_text="Is this the master template for a recurring task series?")
    recurrence_end_date = models.DateField(blank=True, null=True, help_text="Date when the recurring series should end.")
    parent_task = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='occurrences', help_text="Link to the master recurring task if this is an occurrence.")
    next_occurrence_date = models.DateTimeField(blank=True, null=True, help_text="For template tasks, when the next occurrence should be generated.")


    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    updated_at = models.DateTimeField(default=timezone.now, blank=True, null=True)
    
    class Meta:
        db_table = 'tasks'
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['due_date', 'priority']
        indexes = [
            models.Index(fields=['due_date']),
            models.Index(fields=['status']),
            models.Index(fields=['priority']),
            models.Index(fields=['created_by']),
            models.Index(fields=['assigned_to']), # Index on ForeignKey is often created automatically by DB
            models.Index(fields=['is_recurring_template', 'next_occurrence_date']),
            models.Index(fields=['status', 'due_date']),      # Composite for common queries
            models.Index(fields=['assigned_to', 'status']),   # Composite for user tasks
            models.Index(fields=['created_by', 'status']),    # Composite for created tasks
            models.Index(fields=['office', 'status']),        # Composite for office tasks
        ]
    
    def __str__(self):
        return self.title if self.title else f"Task {self.id}"
    
    @property
    def is_completed(self):
        """Return whether the task is completed."""
        return self.status == 'completed' or self.completed_at is not None
    
    @property
    def is_overdue(self):
        """Return whether the task is overdue."""
        if not self.due_date:
            return False
        if self.is_completed:
            return False
        return self.due_date < timezone.now().date()
    
    def get_absolute_url(self):
        """Return the URL to access a detail record for this task."""
        from django.urls import reverse
        return reverse('tasks:task_detail', args=[str(self.id)])
    
    def calculate_next_occurrence(self):
        """Calculate the next occurrence date based on recurring pattern."""
        if not self.recurring_pattern or not self.is_recurring_template:
            return None
            
        pattern = self.recurring_pattern
        frequency = pattern.get('frequency')
        interval = pattern.get('interval', 1)
        
        # Start from next_occurrence_date if set, otherwise from due_date
        base_date = self.next_occurrence_date or timezone.now()
        if isinstance(base_date, datetime):
            base_date = base_date.date()
        
        if frequency == 'daily':
            next_date = base_date + timedelta(days=interval)
        elif frequency == 'weekly':
            weekdays = pattern.get('weekdays', [])
            if weekdays:
                # Find next occurrence on specified weekdays
                next_date = base_date + timedelta(days=1)
                while next_date.weekday() not in weekdays:
                    next_date += timedelta(days=1)
            else:
                next_date = base_date + timedelta(weeks=interval)
        elif frequency == 'monthly':
            day_of_month = pattern.get('day_of_month')
            if day_of_month:
                next_date = base_date.replace(day=day_of_month) + relativedelta(months=interval)
            else:
                next_date = base_date + relativedelta(months=interval)
        else:
            return None
            
        # Check if we've passed the end date
        if self.recurrence_end_date and next_date > self.recurrence_end_date:
            return None
            
        return timezone.make_aware(datetime.combine(next_date, datetime.min.time()))
    
    def generate_next_occurrence(self):
        """Generate the next occurrence task instance."""
        if not self.is_recurring_template:
            return None
            
        next_date = self.calculate_next_occurrence()
        if not next_date:
            return None
            
        # Create new task instance
        occurrence = Task.objects.create(
            title=self.title,
            description=self.description,
            due_date=next_date.date(),
            due_time=self.due_time,
            due_time_details=self.due_time_details,
            reminder_time=self.reminder_time,
            reminder_option=self.reminder_option,
            priority=self.priority,
            status='pending',
            category=self.category,
            type=self.type,
            person=self.person,
            church=self.church,
            contact=self.contact,
            created_by=self.created_by,
            assigned_to=self.assigned_to,
            office=self.office,
            parent_task=self,
            is_recurring_template=False,
            google_calendar_sync_enabled=self.google_calendar_sync_enabled,
        )
        
        # Update next occurrence date on template
        self.next_occurrence_date = self.calculate_next_occurrence()
        self.save(update_fields=['next_occurrence_date'])
        
        return occurrence
    
    @classmethod
    def generate_pending_occurrences(cls, days_ahead=7):
        """Generate all pending recurring task occurrences for the next N days."""
        cutoff_date = timezone.now() + timedelta(days=days_ahead)
        
        # Find all recurring templates that need new occurrences
        templates = cls.objects.filter(
            is_recurring_template=True,
            next_occurrence_date__lte=cutoff_date
        ).exclude(
            recurrence_end_date__lt=timezone.now().date()
        )
        
        generated_count = 0
        for template in templates:
            while (template.next_occurrence_date and 
                   template.next_occurrence_date <= cutoff_date and 
                   (not template.recurrence_end_date or 
                    template.next_occurrence_date.date() <= template.recurrence_end_date)):
                
                occurrence = template.generate_next_occurrence()
                if occurrence:
                    generated_count += 1
                else:
                    break
                    
        return generated_count
