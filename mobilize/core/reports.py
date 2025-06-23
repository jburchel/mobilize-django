"""
Report generation utilities for the Mobilize CRM.

This module provides functionality to generate various reports in different formats
(CSV, Excel, PDF) based on user permissions and data access levels.
"""
import csv
import io
from datetime import datetime, timedelta
from django.http import HttpResponse
from django.template.loader import render_to_string
from mobilize.core.permissions import get_data_access_manager


class ReportGenerator:
    """
    Generates reports based on user permissions and data access.
    """
    
    def __init__(self, user, view_mode='default'):
        """
        Initialize the report generator.
        
        Args:
            user: The current user
            view_mode: The viewing mode for data access
        """
        self.user = user
        self.access_manager = get_data_access_manager(type('obj', (object,), {
            'user': user, 
            'GET': {'view_mode': view_mode}
        })())
    
    def generate_people_report(self, format='csv'):
        """
        Generate a people report in the specified format.
        
        Args:
            format: Export format ('csv', 'excel')
            
        Returns:
            HttpResponse with the report data
        """
        people_queryset = self.access_manager.get_people_queryset()
        
        if format == 'csv':
            return self._generate_people_csv(people_queryset)
        elif format == 'excel':
            return self._generate_people_excel(people_queryset)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def generate_churches_report(self, format='csv'):
        """
        Generate a churches report in the specified format.
        
        Args:
            format: Export format ('csv', 'excel')
            
        Returns:
            HttpResponse with the report data
        """
        churches_queryset = self.access_manager.get_churches_queryset()
        
        if format == 'csv':
            return self._generate_churches_csv(churches_queryset)
        elif format == 'excel':
            return self._generate_churches_excel(churches_queryset)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def generate_tasks_report(self, format='csv', status_filter=None):
        """
        Generate a tasks report in the specified format.
        
        Args:
            format: Export format ('csv', 'excel')
            status_filter: Optional status filter ('pending', 'completed', 'overdue')
            
        Returns:
            HttpResponse with the report data
        """
        tasks_queryset = self.access_manager.get_tasks_queryset()
        
        # Apply status filter
        if status_filter == 'pending':
            tasks_queryset = tasks_queryset.filter(status='pending')
        elif status_filter == 'completed':
            tasks_queryset = tasks_queryset.filter(status='completed')
        elif status_filter == 'overdue':
            tasks_queryset = tasks_queryset.filter(
                status='pending',
                due_date__lt=datetime.now().date()
            )
        
        if format == 'csv':
            return self._generate_tasks_csv(tasks_queryset)
        elif format == 'excel':
            return self._generate_tasks_excel(tasks_queryset)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def generate_communications_report(self, format='csv', date_range=None):
        """
        Generate a communications report in the specified format.
        
        Args:
            format: Export format ('csv', 'excel')
            date_range: Optional date range filter (days)
            
        Returns:
            HttpResponse with the report data
        """
        communications_queryset = self.access_manager.get_communications_queryset()
        
        # Apply date filter
        if date_range:
            start_date = datetime.now().date() - timedelta(days=date_range)
            communications_queryset = communications_queryset.filter(
                date__gte=start_date
            )
        
        if format == 'csv':
            return self._generate_communications_csv(communications_queryset)
        elif format == 'excel':
            return self._generate_communications_excel(communications_queryset)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def generate_dashboard_summary(self, format='csv'):
        """
        Generate a dashboard summary report.
        
        Args:
            format: Export format ('csv', 'excel')
            
        Returns:
            HttpResponse with the summary data
        """
        # Get summary data
        people_count = self.access_manager.get_people_queryset().count()
        churches_count = self.access_manager.get_churches_queryset().count()
        pending_tasks = self.access_manager.get_tasks_queryset().filter(status='pending').count()
        completed_tasks = self.access_manager.get_tasks_queryset().filter(status='completed').count()
        
        summary_data = [
            ['Metric', 'Count'],
            ['People', people_count],
            ['Churches', churches_count],
            ['Pending Tasks', pending_tasks],
            ['Completed Tasks', completed_tasks],
        ]
        
        if format == 'csv':
            return self._create_csv_response(summary_data, 'dashboard_summary')
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_people_csv(self, queryset):
        """Generate CSV response for people data."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="people_report_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'First Name', 'Last Name', 'Email', 'Phone', 'Pipeline Stage',
            'Priority', 'Assigned To', 'Church', 'Status', 'Last Contact', 'Created Date'
        ])
        
        for person in queryset:
            writer.writerow([
                person.contact.id,
                person.contact.first_name or '',
                person.contact.last_name or '',
                person.contact.email or '',
                person.contact.phone or '',
                person.contact.get_pipeline_stage_name() or '',
                person.contact.get_priority_display() or '',
                person.contact.user.username if person.contact.user else '',
                person.primary_church.name if person.primary_church else '',
                person.contact.get_status_display() or '',
                person.contact.last_contact_date.strftime('%Y-%m-%d') if person.contact.last_contact_date else '',
                person.contact.created_at.strftime('%Y-%m-%d') if person.contact.created_at else '',
            ])
        
        return response
    
    def _generate_churches_csv(self, queryset):
        """Generate CSV response for churches data."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="churches_report_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Name', 'Denomination', 'Website', 'Congregation Size',
            'Pastor Name', 'Pastor Email', 'Pastor Phone', 'Address', 'Created Date'
        ])
        
        for church in queryset:
            writer.writerow([
                church.contact.id,
                church.name or '',
                church.denomination or '',
                church.website or '',
                church.congregation_size or '',
                church.pastor_name or '',
                church.pastor_email or '',
                church.pastor_phone or '',
                church.contact.street_address or '',
                church.contact.created_at.strftime('%Y-%m-%d') if church.contact.created_at else '',
            ])
        
        return response
    
    def _generate_tasks_csv(self, queryset):
        """Generate CSV response for tasks data."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="tasks_report_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Title', 'Description', 'Status', 'Priority', 'Due Date',
            'Assigned To', 'Created By', 'Created Date', 'Completed Date'
        ])
        
        for task in queryset.select_related('assigned_to', 'created_by'):
            writer.writerow([
                task.id,
                task.title or '',
                task.description or '',
                task.status or '',
                task.priority or '',
                task.due_date.strftime('%Y-%m-%d') if task.due_date else '',
                task.assigned_to.get_full_name() if task.assigned_to else '',
                task.created_by.get_full_name() if task.created_by else '',
                task.created_at.strftime('%Y-%m-%d %H:%M') if task.created_at else '',
                task.completed_at.strftime('%Y-%m-%d %H:%M') if task.completed_at else '',
            ])
        
        return response
    
    def _generate_communications_csv(self, queryset):
        """Generate CSV response for communications data."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="communications_report_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Type', 'Subject', 'Direction', 'Date', 'Sender',
            'Person ID', 'Church ID', 'Status'
        ])
        
        for comm in queryset:
            writer.writerow([
                comm.id,
                comm.type or '',
                comm.subject or '',
                comm.direction or '',
                comm.date.strftime('%Y-%m-%d') if comm.date else '',
                comm.sender or '',
                comm.person_id or '',
                comm.church_id or '',
                comm.email_status or '',
            ])
        
        return response
    
    def _create_csv_response(self, data, filename_prefix):
        """Create a CSV response from data array."""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{filename_prefix}_{datetime.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        for row in data:
            writer.writerow(row)
        
        return response
    
    def _generate_people_excel(self, queryset):
        """Generate Excel response for people data (requires openpyxl)."""
        # This would require openpyxl package
        # For now, fallback to CSV
        return self._generate_people_csv(queryset)
    
    def _generate_churches_excel(self, queryset):
        """Generate Excel response for churches data (requires openpyxl)."""
        # This would require openpyxl package
        # For now, fallback to CSV
        return self._generate_churches_csv(queryset)
    
    def _generate_tasks_excel(self, queryset):
        """Generate Excel response for tasks data (requires openpyxl)."""
        # This would require openpyxl package
        # For now, fallback to CSV
        return self._generate_tasks_csv(queryset)
    
    def _generate_communications_excel(self, queryset):
        """Generate Excel response for communications data (requires openpyxl)."""
        # This would require openpyxl package
        # For now, fallback to CSV
        return self._generate_communications_csv(queryset)