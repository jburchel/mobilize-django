"""
Tests for core reports functionality
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from mobilize.core.reports import ReportGenerator
from mobilize.contacts.models import Person
from mobilize.churches.models import Church
from mobilize.admin_panel.models import Office
from mobilize.tasks.models import Task
from mobilize.communications.models import Communication
from datetime import datetime, timedelta
import csv
import io

User = get_user_model()


class ReportGeneratorTests(TestCase):
    """Test cases for ReportGenerator"""
    
    def setUp(self):
        # Create office
        self.office = Office.objects.create(name='Test Office', code='TEST')
        
        # Create user
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='super_admin'
        )
        
        # Create test data
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            pipeline_stage='lead',
            priority='high',
            assigned_to=str(self.user.id),
            status='active',
            user_id=self.user.id
        )
        
        self.church = Church.objects.create(
            name='Test Church',
            denomination='Baptist',
            website='https://testchurch.com',
            congregation_size=150,
            pastor_name='Pastor Smith',
            pastor_email='pastor@testchurch.com',
            pastor_phone='555-1234',
            office_id=self.office.id
        )
        
        self.task = Task.objects.create(
            title='Test Task',
            description='Test task description',
            status='pending',
            priority='medium',
            assigned_to=self.user,
            created_by=self.user,
            due_date=datetime.now().date() + timedelta(days=7)
        )
        
        self.communication = Communication.objects.create(
            type='email',
            subject='Test Email',
            direction='outbound',
            date=datetime.now().date(),
            sender='test@example.com',
            person_id=self.person.id,
            user_id=str(self.user.id)
        )
        
        self.report_generator = ReportGenerator(self.user)
    
    def test_generate_people_report_csv(self):
        """Test generating people report in CSV format"""
        response = self.report_generator.generate_people_report(format='csv')
        
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('people_report_', response['Content-Disposition'])
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Check header row
        self.assertIn('First Name', rows[0])
        self.assertIn('Last Name', rows[0])
        self.assertIn('Email', rows[0])
        
        # Check data row
        self.assertEqual(len(rows), 2)  # Header + 1 data row
        self.assertIn('John', rows[1])
        self.assertIn('Doe', rows[1])
    
    def test_generate_churches_report_csv(self):
        """Test generating churches report in CSV format"""
        response = self.report_generator.generate_churches_report(format='csv')
        
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('churches_report_', response['Content-Disposition'])
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Check header row
        self.assertIn('Name', rows[0])
        self.assertIn('Denomination', rows[0])
        self.assertIn('Website', rows[0])
        
        # Check data row
        self.assertEqual(len(rows), 2)  # Header + 1 data row
        self.assertIn('Test Church', rows[1])
        self.assertIn('Baptist', rows[1])
    
    def test_generate_tasks_report_csv(self):
        """Test generating tasks report in CSV format"""
        response = self.report_generator.generate_tasks_report(format='csv')
        
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('tasks_report_', response['Content-Disposition'])
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Check header row
        self.assertIn('Title', rows[0])
        self.assertIn('Status', rows[0])
        self.assertIn('Priority', rows[0])
        
        # Check data row
        self.assertEqual(len(rows), 2)  # Header + 1 data row
        self.assertIn('Test Task', rows[1])
        self.assertIn('pending', rows[1])
    
    def test_generate_communications_report_csv(self):
        """Test generating communications report in CSV format"""
        response = self.report_generator.generate_communications_report(format='csv')
        
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('communications_report_', response['Content-Disposition'])
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Check header row
        self.assertIn('Type', rows[0])
        self.assertIn('Subject', rows[0])
        self.assertIn('Direction', rows[0])
        
        # Check data row
        self.assertEqual(len(rows), 2)  # Header + 1 data row
        self.assertIn('email', rows[1])
        self.assertIn('Test Email', rows[1])
    
    def test_generate_dashboard_summary_csv(self):
        """Test generating dashboard summary report"""
        response = self.report_generator.generate_dashboard_summary(format='csv')
        
        self.assertIsInstance(response, HttpResponse)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('dashboard_summary_', response['Content-Disposition'])
        
        # Parse CSV content
        content = response.content.decode('utf-8')
        csv_reader = csv.reader(io.StringIO(content))
        rows = list(csv_reader)
        
        # Check header row
        self.assertEqual(rows[0], ['Metric', 'Count'])
        
        # Check data rows
        self.assertGreater(len(rows), 1)
        metrics = {row[0]: row[1] for row in rows[1:]}
        self.assertIn('People', metrics)
        self.assertIn('Churches', metrics)
        self.assertIn('Pending Tasks', metrics)
        self.assertIn('Completed Tasks', metrics)
    
    def test_tasks_report_with_status_filter(self):
        """Test tasks report with status filter"""
        # Create completed task
        Task.objects.create(
            title='Completed Task',
            description='Completed task description',
            status='completed',
            assigned_to=self.user,
            created_by=self.user
        )
        
        # Test pending filter
        response = self.report_generator.generate_tasks_report(
            format='csv', 
            status_filter='pending'
        )
        content = response.content.decode('utf-8')
        self.assertIn('Test Task', content)
        self.assertNotIn('Completed Task', content)
        
        # Test completed filter
        response = self.report_generator.generate_tasks_report(
            format='csv', 
            status_filter='completed'
        )
        content = response.content.decode('utf-8')
        self.assertNotIn('Test Task', content)
        self.assertIn('Completed Task', content)
    
    def test_tasks_report_overdue_filter(self):
        """Test tasks report with overdue filter"""
        # Create overdue task
        Task.objects.create(
            title='Overdue Task',
            description='Overdue task description',
            status='pending',
            assigned_to=self.user,
            created_by=self.user,
            due_date=datetime.now().date() - timedelta(days=1)
        )
        
        response = self.report_generator.generate_tasks_report(
            format='csv', 
            status_filter='overdue'
        )
        content = response.content.decode('utf-8')
        self.assertIn('Overdue Task', content)
        self.assertNotIn('Test Task', content)  # Not overdue
    
    def test_communications_report_with_date_filter(self):
        """Test communications report with date range filter"""
        # Create old communication
        old_comm = Communication.objects.create(
            type='email',
            subject='Old Email',
            direction='inbound',
            date=datetime.now().date() - timedelta(days=10),
            user_id=str(self.user.id)
        )
        
        # Test 7-day filter
        response = self.report_generator.generate_communications_report(
            format='csv', 
            date_range=7
        )
        content = response.content.decode('utf-8')
        self.assertIn('Test Email', content)  # Recent
        self.assertNotIn('Old Email', content)  # Too old
    
    def test_excel_format_fallback(self):
        """Test that Excel format falls back to CSV"""
        response = self.report_generator.generate_people_report(format='excel')
        
        # Should still be CSV format
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('people_report_', response['Content-Disposition'])
    
    def test_unsupported_format_raises_error(self):
        """Test that unsupported format raises ValueError"""
        with self.assertRaises(ValueError):
            self.report_generator.generate_people_report(format='pdf')
        
        with self.assertRaises(ValueError):
            self.report_generator.generate_churches_report(format='json')
        
        with self.assertRaises(ValueError):
            self.report_generator.generate_tasks_report(format='xml')
        
        with self.assertRaises(ValueError):
            self.report_generator.generate_communications_report(format='yaml')
    
    def test_report_generator_with_view_mode(self):
        """Test report generator with different view modes"""
        # Create another user and data
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            role='standard_user'
        )
        
        Person.objects.create(
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com',
            assigned_to=str(other_user.id),
            user_id=other_user.id
        )
        
        # Test with my_only view mode
        my_only_generator = ReportGenerator(self.user, view_mode='my_only')
        response = my_only_generator.generate_people_report(format='csv')
        
        content = response.content.decode('utf-8')
        # Should only include people assigned to this user
        self.assertIn('John', content)
        self.assertNotIn('Jane', content)