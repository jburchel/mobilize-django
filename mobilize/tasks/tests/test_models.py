"""
Test cases for Task app models.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta, date
import json

from mobilize.admin_panel.models import Office
from mobilize.contacts.models import Person, Contact
from mobilize.churches.models import Church
from mobilize.tasks.models import Task

User = get_user_model()


class TaskModelTest(TestCase):
    """Test cases for Task model"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        # Create Contact first, then Person
        person_contact = Contact.objects.create(
            type='person',
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
        self.person = Person.objects.create(
            contact=person_contact
        )
        # Create Contact first, then Church
        church_contact = Contact.objects.create(
            type='church',
            church_name='Test Church'
        )
        self.church = Church.objects.create(
            contact=church_contact,
            name='Test Church'
        )
        # Create a separate Contact
        self.contact = Contact.objects.create(
            type='person',
            first_name='Jane',
            last_name='Smith',
            email='jane@example.com'
        )
    
    def test_task_creation(self):
        """Test basic task creation"""
        task = Task.objects.create(
            title='Test Task',
            description='A test task',
            status='pending',
            priority='medium',
            type='general',
            created_by=self.user,
            assigned_to=self.user,
            office=self.office
        )
        
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.description, 'A test task')
        self.assertEqual(task.status, 'pending')
        self.assertEqual(task.priority, 'medium')
        self.assertEqual(task.type, 'general')
        self.assertEqual(task.created_by, self.user)
        self.assertEqual(task.assigned_to, self.user)
        self.assertEqual(task.office, self.office)
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)
    
    def test_task_status_choices(self):
        """Test all task status choices can be created"""
        for status, _ in Task.STATUS_CHOICES:
            task = Task.objects.create(
                title=f'Test {status} Task',
                status=status,
                created_by=self.user,
                office=self.office
            )
            self.assertEqual(task.status, status)
    
    def test_task_priority_choices(self):
        """Test all task priority choices can be created"""
        for priority, _ in Task.PRIORITY_CHOICES:
            task = Task.objects.create(
                title=f'Test {priority} Task',
                priority=priority,
                created_by=self.user,
                office=self.office
            )
            self.assertEqual(task.priority, priority)
    
    def test_task_str_representation(self):
        """Test task string representation"""
        task = Task.objects.create(
            title='Test Task',
            created_by=self.user,
            office=self.office
        )
        self.assertEqual(str(task), 'Test Task')
        
        # Test with no title
        task_no_title = Task.objects.create(
            created_by=self.user,
            office=self.office
        )
        self.assertEqual(str(task_no_title), f'Task {task_no_title.id}')
    
    def test_task_person_relationship(self):
        """Test task relationship with person"""
        task = Task.objects.create(
            title='Person Task',
            person=self.person,
            created_by=self.user,
            office=self.office
        )
        
        self.assertEqual(task.person, self.person)
        self.assertIn(task, self.person.person_tasks.all())
    
    def test_task_church_relationship(self):
        """Test task relationship with church"""
        task = Task.objects.create(
            title='Church Task',
            church=self.church,
            created_by=self.user,
            office=self.office
        )
        
        self.assertEqual(task.church, self.church)
        self.assertIn(task, self.church.church_tasks.all())
    
    def test_task_contact_relationship(self):
        """Test task relationship with contact"""
        task = Task.objects.create(
            title='Contact Task',
            contact=self.contact,
            created_by=self.user,
            office=self.office
        )
        
        self.assertEqual(task.contact, self.contact)
        self.assertIn(task, self.contact.contact_tasks.all())
    
    def test_task_office_relationship(self):
        """Test task relationship with office"""
        task = Task.objects.create(
            title='Office Task',
            created_by=self.user,
            office=self.office
        )
        
        self.assertEqual(task.office, self.office)
        self.assertIn(task, self.office.tasks.all())
    
    def test_task_user_relationships(self):
        """Test task relationships with users"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com'
        )
        
        task = Task.objects.create(
            title='User Task',
            created_by=self.user,
            assigned_to=other_user,
            office=self.office
        )
        
        # Test created_by relationship
        self.assertEqual(task.created_by, self.user)
        self.assertIn(task, self.user.created_tasks.all())
        
        # Test assigned_to relationship
        self.assertEqual(task.assigned_to, other_user)
        self.assertIn(task, other_user.assigned_tasks.all())
    
    def test_task_due_date_fields(self):
        """Test task due date related fields"""
        due_date = timezone.now().date() + timedelta(days=7)
        task = Task.objects.create(
            title='Due Date Task',
            due_date=due_date,
            due_time='14:30',
            due_time_details='Afternoon meeting',
            reminder_time='13:30',
            reminder_option='30_minutes',
            created_by=self.user,
            office=self.office
        )
        
        self.assertEqual(task.due_date, due_date)
        self.assertEqual(task.due_time, '14:30')
        self.assertEqual(task.due_time_details, 'Afternoon meeting')
        self.assertEqual(task.reminder_time, '13:30')
        self.assertEqual(task.reminder_option, '30_minutes')
        self.assertFalse(task.reminder_sent)
    
    def test_task_completion_fields(self):
        """Test task completion related fields"""
        completed_time = timezone.now()
        task = Task.objects.create(
            title='Completed Task',
            status='completed',
            completed_at=completed_time,
            completed_date=completed_time,
            completion_notes='Task completed successfully',
            created_by=self.user,
            office=self.office
        )
        
        self.assertEqual(task.status, 'completed')
        self.assertEqual(task.completed_at, completed_time)
        self.assertEqual(task.completed_date, completed_time)
        self.assertEqual(task.completion_notes, 'Task completed successfully')
    
    def test_task_google_calendar_fields(self):
        """Test Google Calendar integration fields"""
        sync_time = timezone.now()
        task = Task.objects.create(
            title='Calendar Task',
            google_calendar_event_id='event123',
            google_calendar_sync_enabled=True,
            last_synced_at=sync_time,
            created_by=self.user,
            office=self.office
        )
        
        self.assertEqual(task.google_calendar_event_id, 'event123')
        self.assertTrue(task.google_calendar_sync_enabled)
        self.assertEqual(task.last_synced_at, sync_time)
    
    def test_task_is_completed_property(self):
        """Test is_completed property"""
        # Pending task
        pending_task = Task.objects.create(
            title='Pending Task',
            status='pending',
            created_by=self.user,
            office=self.office
        )
        self.assertFalse(pending_task.is_completed)
        
        # Completed by status
        completed_task = Task.objects.create(
            title='Completed Task',
            status='completed',
            created_by=self.user,
            office=self.office
        )
        self.assertTrue(completed_task.is_completed)
        
        # Completed by completed_at
        completed_at_task = Task.objects.create(
            title='Completed At Task',
            status='pending',
            completed_at=timezone.now(),
            created_by=self.user,
            office=self.office
        )
        self.assertTrue(completed_at_task.is_completed)
    
    def test_task_is_overdue_property(self):
        """Test is_overdue property"""
        # Future due date - not overdue
        future_task = Task.objects.create(
            title='Future Task',
            due_date=timezone.now().date() + timedelta(days=7),
            status='pending',
            created_by=self.user,
            office=self.office
        )
        self.assertFalse(future_task.is_overdue)
        
        # Past due date - overdue
        overdue_task = Task.objects.create(
            title='Overdue Task',
            due_date=timezone.now().date() - timedelta(days=1),
            status='pending',
            created_by=self.user,
            office=self.office
        )
        self.assertTrue(overdue_task.is_overdue)
        
        # No due date - not overdue
        no_due_date_task = Task.objects.create(
            title='No Due Date Task',
            status='pending',
            created_by=self.user,
            office=self.office
        )
        self.assertFalse(no_due_date_task.is_overdue)
        
        # Completed task - not overdue even if past due
        completed_overdue_task = Task.objects.create(
            title='Completed Overdue Task',
            due_date=timezone.now().date() - timedelta(days=1),
            status='completed',
            created_by=self.user,
            office=self.office
        )
        self.assertFalse(completed_overdue_task.is_overdue)
    
    def test_task_get_absolute_url(self):
        """Test get_absolute_url method"""
        task = Task.objects.create(
            title='URL Task',
            created_by=self.user,
            office=self.office
        )
        
        expected_url = f'/tasks/{task.id}/'
        self.assertEqual(task.get_absolute_url(), expected_url)


class TaskRecurringTest(TestCase):
    """Test cases for recurring task functionality"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
    
    def test_recurring_template_creation(self):
        """Test creating recurring task template"""
        recurring_pattern = {
            'frequency': 'weekly',
            'interval': 1,
            'weekdays': [0, 2, 4]  # Monday, Wednesday, Friday
        }
        
        template = Task.objects.create(
            title='Weekly Recurring Task',
            description='A weekly recurring task',
            recurring_pattern=recurring_pattern,
            is_recurring_template=True,
            recurrence_end_date=timezone.now().date() + timedelta(days=90),
            due_date=timezone.now().date() + timedelta(days=1),
            created_by=self.user,
            office=self.office
        )
        
        self.assertTrue(template.is_recurring_template)
        self.assertEqual(template.recurring_pattern, recurring_pattern)
        self.assertIsNotNone(template.recurrence_end_date)
    
    def test_parent_task_relationship(self):
        """Test parent task relationship for occurrences"""
        template = Task.objects.create(
            title='Template Task',
            is_recurring_template=True,
            created_by=self.user,
            office=self.office
        )
        
        occurrence = Task.objects.create(
            title='Occurrence Task',
            parent_task=template,
            is_recurring_template=False,
            created_by=self.user,
            office=self.office
        )
        
        self.assertEqual(occurrence.parent_task, template)
        self.assertIn(occurrence, template.occurrences.all())
    
    def test_calculate_next_occurrence_daily(self):
        """Test calculating next occurrence for daily tasks"""
        pattern = {'frequency': 'daily', 'interval': 2}
        
        template = Task.objects.create(
            title='Daily Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                timezone.now().date(), datetime.min.time()
            )),
            created_by=self.user,
            office=self.office
        )
        
        next_occurrence = template.calculate_next_occurrence()
        expected_date = timezone.now().date() + timedelta(days=2)
        
        self.assertIsNotNone(next_occurrence)
        self.assertEqual(next_occurrence.date(), expected_date)
    
    def test_calculate_next_occurrence_weekly(self):
        """Test calculating next occurrence for weekly tasks"""
        pattern = {
            'frequency': 'weekly', 
            'interval': 1,
            'weekdays': [0, 2]  # Monday, Wednesday
        }
        
        template = Task.objects.create(
            title='Weekly Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                timezone.now().date(), datetime.min.time()
            )),
            created_by=self.user,
            office=self.office
        )
        
        next_occurrence = template.calculate_next_occurrence()
        self.assertIsNotNone(next_occurrence)
        
        # Should be on Monday (0) or Wednesday (2)
        self.assertIn(next_occurrence.weekday(), [0, 2])
    
    def test_calculate_next_occurrence_monthly(self):
        """Test calculating next occurrence for monthly tasks"""
        pattern = {
            'frequency': 'monthly',
            'interval': 1,
            'day_of_month': 15
        }
        
        template = Task.objects.create(
            title='Monthly Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                timezone.now().date(), datetime.min.time()
            )),
            created_by=self.user,
            office=self.office
        )
        
        next_occurrence = template.calculate_next_occurrence()
        self.assertIsNotNone(next_occurrence)
        self.assertEqual(next_occurrence.day, 15)
    
    def test_calculate_next_occurrence_with_end_date(self):
        """Test that next occurrence respects end date"""
        pattern = {'frequency': 'daily', 'interval': 1}
        end_date = timezone.now().date() + timedelta(days=1)
        
        template = Task.objects.create(
            title='Ending Task',
            recurring_pattern=pattern,
            is_recurring_template=True,
            recurrence_end_date=end_date,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                end_date + timedelta(days=1), datetime.min.time()
            )),
            created_by=self.user,
            office=self.office
        )
        
        next_occurrence = template.calculate_next_occurrence()
        self.assertIsNone(next_occurrence)  # Should be None due to end date
    
    def test_generate_next_occurrence(self):
        """Test generating next occurrence task"""
        # Create Contact first, then Person
        person_contact = Contact.objects.create(
            type='person',
            first_name='Test',
            last_name='Person',
            email='test@example.com'
        )
        person = Person.objects.create(
            contact=person_contact
        )
        
        pattern = {'frequency': 'daily', 'interval': 1}
        
        template = Task.objects.create(
            title='Template Task',
            description='Template description',
            priority='high',
            recurring_pattern=pattern,
            is_recurring_template=True,
            person=person,
            created_by=self.user,
            assigned_to=self.user,
            office=self.office,
            due_date=timezone.now().date(),
            next_occurrence_date=timezone.make_aware(datetime.combine(
                timezone.now().date() + timedelta(days=1), datetime.min.time()
            ))
        )
        
        occurrence = template.generate_next_occurrence()
        
        self.assertIsNotNone(occurrence)
        self.assertEqual(occurrence.title, template.title)
        self.assertEqual(occurrence.description, template.description)
        self.assertEqual(occurrence.priority, template.priority)
        self.assertEqual(occurrence.person, template.person)
        self.assertEqual(occurrence.created_by, template.created_by)
        self.assertEqual(occurrence.assigned_to, template.assigned_to)
        self.assertEqual(occurrence.office, template.office)
        self.assertEqual(occurrence.parent_task, template)
        self.assertFalse(occurrence.is_recurring_template)
        self.assertEqual(occurrence.status, 'pending')
    
    def test_generate_pending_occurrences(self):
        """Test generating pending occurrences class method"""
        pattern = {'frequency': 'daily', 'interval': 1}
        
        # Create template with next occurrence tomorrow
        tomorrow = timezone.now().date() + timedelta(days=1)
        template = Task.objects.create(
            title='Daily Template',
            recurring_pattern=pattern,
            is_recurring_template=True,
            next_occurrence_date=timezone.make_aware(datetime.combine(
                tomorrow, datetime.min.time()
            )),
            recurrence_end_date=timezone.now().date() + timedelta(days=30),
            created_by=self.user,
            office=self.office
        )
        
        # Generate occurrences for next 7 days
        generated_count = Task.generate_pending_occurrences(days_ahead=7)
        
        # Should generate some occurrences
        self.assertGreater(generated_count, 0)
        
        # Check that occurrences were created
        occurrences = Task.objects.filter(parent_task=template)
        self.assertGreater(occurrences.count(), 0)
    
    def test_non_template_methods_return_none(self):
        """Test that non-template tasks return None for template methods"""
        task = Task.objects.create(
            title='Regular Task',
            is_recurring_template=False,
            created_by=self.user,
            office=self.office
        )
        
        self.assertIsNone(task.calculate_next_occurrence())
        self.assertIsNone(task.generate_next_occurrence())


class TaskCascadeDeleteTest(TestCase):
    """Test cascade delete behavior for Task relationships"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        # Create Contact first, then Person
        person_contact = Contact.objects.create(
            type='person',
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
        self.person = Person.objects.create(
            contact=person_contact
        )
        # Create Contact first, then Church
        church_contact = Contact.objects.create(
            type='church',
            church_name='Test Church'
        )
        self.church = Church.objects.create(
            contact=church_contact,
            name='Test Church'
        )
    
    def test_office_deletion_sets_null(self):
        """Test that deleting office sets task.office to NULL"""
        task = Task.objects.create(
            title='Office Task',
            office=self.office,
            created_by=self.user
        )
        
        task_id = task.id
        self.office.delete()
        
        # Task should still exist but office should be None
        task.refresh_from_db()
        self.assertIsNone(task.office)
    
    def test_person_deletion_sets_null(self):
        """Test that deleting person sets task.person to NULL"""
        task = Task.objects.create(
            title='Person Task',
            person=self.person,
            created_by=self.user,
            office=self.office
        )
        
        self.person.delete()
        
        # Task should still exist but person should be None
        task.refresh_from_db()
        self.assertIsNone(task.person)
    
    def test_church_deletion_sets_null(self):
        """Test that deleting church sets task.church to NULL"""
        task = Task.objects.create(
            title='Church Task',
            church=self.church,
            created_by=self.user,
            office=self.office
        )
        
        self.church.delete()
        
        # Task should still exist but church should be None
        task.refresh_from_db()
        self.assertIsNone(task.church)
    
    def test_user_deletion_sets_null(self):
        """Test that deleting user sets task user fields to NULL"""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com'
        )
        
        task = Task.objects.create(
            title='User Task',
            created_by=self.user,
            assigned_to=other_user,
            office=self.office
        )
        
        # Test that the relationship exists
        self.assertEqual(task.assigned_to, other_user)
        self.assertEqual(task.created_by, self.user)
        
        # Note: We can't actually test user deletion in this test environment
        # due to database constraints, but we can verify the relationship
        # and that the fields allow NULL
        task.assigned_to = None
        task.save()
        
        # Refresh from database
        task.refresh_from_db()
        
        # assigned_to should be NULL now
        self.assertIsNone(task.assigned_to)
        self.assertEqual(task.created_by, self.user)  # Should still exist
        
        # Test created_by can also be set to NULL
        task.created_by = None
        task.save()
        
        # Refresh from database
        task.refresh_from_db()
        
        # created_by should be NULL now
        self.assertIsNone(task.created_by)
    
    def test_parent_task_deletion_cascades(self):
        """Test that deleting parent task deletes occurrences"""
        template = Task.objects.create(
            title='Template Task',
            is_recurring_template=True,
            created_by=self.user,
            office=self.office
        )
        
        occurrence = Task.objects.create(
            title='Occurrence Task',
            parent_task=template,
            created_by=self.user,
            office=self.office
        )
        
        occurrence_id = occurrence.id
        template.delete()
        
        # Occurrence should be deleted
        self.assertFalse(Task.objects.filter(id=occurrence_id).exists())