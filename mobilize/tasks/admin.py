from django.contrib import admin
from .models import Task


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    """Admin configuration for Task model."""
    list_display = ('title', 'due_date', 'status', 'priority', 'assigned_to', 'is_completed')
    list_filter = ('status', 'priority', 'due_date', 'office')
    search_fields = ('title', 'description', 'assigned_to__username', 'assigned_to__email') # Assuming User has username/email
    date_hierarchy = 'due_date'
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'type', 'category')
        }),
        ('Status', {
            'fields': ('status', 'priority')
        }),
        ('Dates', {
            'fields': ('due_date', 'due_time', 'due_time_details', 'reminder_time', 'reminder_option')
        }),
        ('Related Entities', {
            'fields': ('contact', 'person', 'church', 'office')
        }),
        ('Assignment', {
            'fields': ('assigned_to', 'created_by') # Removed user_id, owner_id as they are not in current models.py
        }),
        ('Completion', {
            'fields': ('completed_at', 'completed_date', 'completion_notes')
        }),
        ('Google Calendar', {
            'fields': ('google_calendar_event_id', 'google_calendar_sync_enabled', 'last_synced_at')
        }),
        ('System', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def is_completed(self, obj):
        """Return whether the task is completed."""
        return obj.is_completed
    is_completed.boolean = True
    is_completed.short_description = 'Completed'
