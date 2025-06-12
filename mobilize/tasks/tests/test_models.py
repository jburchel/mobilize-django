"""
Tests for tasks models
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from mobilize.tasks.models import Task
from mobilize.contacts.models import Person
from mobilize.churches.models import Church

User = get_user_model()


class TaskModelTests(TestCase):
    """Test cases for the Task model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            role='user'
        )
        
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com',
            user=self.user
        )
        
        self.church = Church.objects.create(
            name='Test Church',
            location='Test City',
            user=self.user
        )
        
        self.task_data = {
            'title': 'Test Task',
            'description': 'This is a test task',
            'status': 'pending',
            'priority': 'medium',
            'due_date': timezone.now() + timedelta(days=7),
            'assigned_to': self.user,
            'created_by': self.user,
        }
    
    def test_create_basic_task(self):
        """Test creating a basic task"""
        task = Task.objects.create(**self.task_data)
        
        self.assertEqual(task.title, 'Test Task')
        self.assertEqual(task.description, 'This is a test task')
        self.assertEqual(task.status, 'pending')
        self.assertEqual(task.priority, 'medium')
        self.assertEqual(task.assigned_to, self.user)
        self.assertEqual(task.created_by, self.user)
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)
    
    def test_task_string_representation(self):
        """Test task string representation"""
        task = Task.objects.create(**self.task_data)
        self.assertEqual(str(task), 'Test Task')
    
    def test_task_status_choices(self):
        """Test task status choices"""
        valid_statuses = ['pending', 'in_progress', 'completed']
        
        for status in valid_statuses:
            task_data = self.task_data.copy()
            task_data['title'] = f'Task {status}'
            task_data['status'] = status
            
            task = Task.objects.create(**task_data)
            self.assertEqual(task.status, status)
    
    def test_task_priority_choices(self):
        """Test task priority choices"""
        valid_priorities = ['low', 'medium', 'high']
        
        for priority in valid_priorities:
            task_data = self.task_data.copy()
            task_data['title'] = f'Task {priority}'
            task_data['priority'] = priority
            
            task = Task.objects.create(**task_data)
            self.assertEqual(task.priority, priority)
    
    def test_task_with_person_association(self):
        """Test task associated with a person"""
        task_data = self.task_data.copy()
        task_data['related_person'] = self.person
        
        task = Task.objects.create(**task_data)
        
        self.assertEqual(task.related_person, self.person)
        self.assertIsNone(task.related_church)
    
    def test_task_with_church_association(self):
        """Test task associated with a church"""
        task_data = self.task_data.copy()
        task_data['related_church'] = self.church
        
        task = Task.objects.create(**task_data)
        
        self.assertEqual(task.related_church, self.church)
        self.assertIsNone(task.related_person)
    
    def test_task_completion(self):
        """Test marking task as completed"""
        task = Task.objects.create(**self.task_data)
        
        # Initially not completed
        self.assertEqual(task.status, 'pending')
        self.assertIsNone(task.completed_at)
        
        # Mark as completed
        task.status = 'completed'
        task.completed_at = timezone.now()
        task.save()
        
        self.assertEqual(task.status, 'completed')
        self.assertIsNotNone(task.completed_at)
    
    def test_task_due_date_validation(self):
        """Test task due date validation"""
        # Task with future due date should be valid
        future_date = timezone.now() + timedelta(days=5)
        task_data = self.task_data.copy()
        task_data['due_date'] = future_date
        
        task = Task.objects.create(**task_data)
        self.assertEqual(task.due_date, future_date)
        
        # Task with past due date should still be created (overdue task)
        past_date = timezone.now() - timedelta(days=1)
        task_data['title'] = 'Overdue Task'
        task_data['due_date'] = past_date
        
        overdue_task = Task.objects.create(**task_data)
        self.assertEqual(overdue_task.due_date, past_date)
    
    def test_recurring_task_fields(self):
        """Test recurring task functionality"""
        task_data = self.task_data.copy()
        task_data.update({
            'is_recurring': True,
            'recurrence_pattern': 'weekly',
            'recurrence_interval': 1,
            'recurrence_end_date': timezone.now() + timedelta(days=90)
        })
        
        task = Task.objects.create(**task_data)
        
        self.assertTrue(task.is_recurring)
        self.assertEqual(task.recurrence_pattern, 'weekly')
        self.assertEqual(task.recurrence_interval, 1)
        self.assertIsNotNone(task.recurrence_end_date)
    
    def test_task_ordering(self):
        """Test task ordering by due date and priority"""
        # Create tasks with different due dates and priorities
        high_priority_task = Task.objects.create(
            title='High Priority',
            priority='high',
            due_date=timezone.now() + timedelta(days=1),
            assigned_to=self.user,
            created_by=self.user
        )
        
        low_priority_task = Task.objects.create(
            title='Low Priority',
            priority='low',
            due_date=timezone.now() + timedelta(days=2),
            assigned_to=self.user,
            created_by=self.user
        )
        
        # Check that we can order by priority and due date
        tasks_by_priority = Task.objects.order_by('-priority')
        tasks_by_due_date = Task.objects.order_by('due_date')
        
        self.assertGreater(len(tasks_by_priority), 0)
        self.assertGreater(len(tasks_by_due_date), 0)
    
    def test_task_user_relationships(self):
        """Test task relationships with users"""
        task = Task.objects.create(**self.task_data)
        
        # Test assigned_to relationship
        self.assertEqual(task.assigned_to, self.user)
        
        # Test created_by relationship
        self.assertEqual(task.created_by, self.user)
        
        # Tasks should be accessible from user
        user_assigned_tasks = Task.objects.filter(assigned_to=self.user)
        user_created_tasks = Task.objects.filter(created_by=self.user)
        
        self.assertIn(task, user_assigned_tasks)
        self.assertIn(task, user_created_tasks)
    
    def test_task_auto_timestamps(self):
        """Test that timestamps are automatically set"""
        task = Task.objects.create(**self.task_data)
        
        self.assertIsNotNone(task.created_at)
        self.assertIsNotNone(task.updated_at)
        
        # Test that updated_at changes when task is modified
        original_updated_at = task.updated_at
        
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.1)
        
        task.title = 'Updated Task Title'
        task.save()
        
        # updated_at should be different
        self.assertNotEqual(task.updated_at, original_updated_at)