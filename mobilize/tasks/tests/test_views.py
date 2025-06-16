"""
Test cases for Task app views.
"""

from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta
import json

from mobilize.admin_panel.models import Office
from mobilize.contacts.models import Person
from mobilize.churches.models import Church
from mobilize.tasks.models import Task

User = get_user_model()


class TaskListViewTest(TestCase):
    """Test cases for task list view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        
        # Create test tasks
        self.pending_task = Task.objects.create(
            title='Pending Task',
            status='pending',
            priority='medium',
            due_date=timezone.now().date() + timedelta(days=7),
            created_by=self.user,
            assigned_to=self.user,
            office=self.office
        )
        
        self.completed_task = Task.objects.create(
            title='Completed Task',
            status='completed',
            priority='high',
            completed_at=timezone.now(),
            created_by=self.user,
            assigned_to=self.user,
            office=self.office
        )
    
    def test_task_list_requires_login(self):
        """Test that task list requires authentication"""
        url = reverse('tasks:task_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_task_list_view_authenticated(self):
        """Test task list view for authenticated user"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.pending_task.title)
        self.assertContains(response, self.completed_task.title)
    
    def test_task_list_ordering(self):
        """Test that tasks are ordered correctly"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_list')
        response = self.client.get(url)
        
        tasks = response.context['tasks']
        # Pending tasks should come before completed tasks
        task_statuses = [task.status for task in tasks]
        pending_indices = [i for i, status in enumerate(task_statuses) if status == 'pending']
        completed_indices = [i for i, status in enumerate(task_statuses) if status == 'completed']
        
        if pending_indices and completed_indices:
            self.assertLess(max(pending_indices), min(completed_indices))
    
    def test_task_list_pagination(self):
        """Test task list pagination"""
        # Create many tasks to test pagination
        for i in range(20):
            Task.objects.create(
                title=f'Task {i}',
                created_by=self.user,
                office=self.office
            )
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        # Should paginate at 15 tasks per page
        self.assertEqual(len(response.context['tasks']), 15)


class TaskDetailViewTest(TestCase):
    """Test cases for task detail view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            status='pending',
            priority='medium',
            created_by=self.user,
            assigned_to=self.user,
            office=self.office
        )
    
    def test_task_detail_requires_login(self):
        """Test that task detail requires authentication"""
        url = reverse('tasks:task_detail', kwargs={'pk': self.task.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_task_detail_view(self):
        """Test task detail view"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_detail', kwargs={'pk': self.task.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.title)
        self.assertContains(response, self.task.description)
        self.assertEqual(response.context['task'], self.task)
    
    def test_task_detail_nonexistent(self):
        """Test task detail with nonexistent task"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_detail', kwargs={'pk': 99999})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 404)


class TaskCreateViewTest(TestCase):
    """Test cases for task creation view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
    
    def test_task_create_requires_login(self):
        """Test that task creation requires authentication"""
        url = reverse('tasks:task_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_task_create_get(self):
        """Test task creation form display"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_create')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="title"')
        self.assertContains(response, 'name="description"')
        self.assertContains(response, 'name="priority"')
        self.assertContains(response, 'name="status"')
    
    def test_task_create_post_success(self):
        """Test successful task creation via POST"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_create')
        
        task_data = {
            'title': 'New Task',
            'description': 'New task description',
            'priority': 'high',
            'status': 'pending',
            'due_date': (timezone.now().date() + timedelta(days=5)),
            'office': self.office.id,
            'assigned_to': self.user.id
        }
        
        response = self.client.post(url, task_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tasks:task_list'))
        
        # Check task was created
        new_task = Task.objects.filter(title='New Task').first()
        self.assertIsNotNone(new_task)
        self.assertEqual(new_task.created_by, self.user)
        self.assertEqual(new_task.description, 'New task description')
        self.assertEqual(new_task.priority, 'high')
    
    def test_task_create_recurring_template(self):
        """Test creating recurring task template"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_create')
        
        recurring_pattern = {
            'frequency': 'weekly',
            'interval': 1,
            'weekdays': [0, 2]  # Monday, Wednesday
        }
        
        task_data = {
            'title': 'Recurring Task',
            'description': 'A recurring task',
            'priority': 'medium',
            'status': 'pending',
            'is_recurring_template': True,
            'recurring_pattern': json.dumps(recurring_pattern),
            'recurrence_end_date': (timezone.now().date() + timedelta(days=90)),
            'office': self.office.id,
            'assigned_to': self.user.id
        }
        
        response = self.client.post(url, task_data)
        
        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)
        
        # Check recurring task was created
        recurring_task = Task.objects.filter(title='Recurring Task').first()
        self.assertIsNotNone(recurring_task)
        self.assertTrue(recurring_task.is_recurring_template)
        self.assertIsNotNone(recurring_task.next_occurrence_date)


class TaskUpdateViewTest(TestCase):
    """Test cases for task update view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        self.task = Task.objects.create(
            title='Test Task',
            description='Test description',
            status='pending',
            priority='medium',
            created_by=self.user,
            assigned_to=self.user,
            office=self.office
        )
    
    def test_task_update_requires_login(self):
        """Test that task update requires authentication"""
        url = reverse('tasks:task_update', kwargs={'pk': self.task.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_task_update_get(self):
        """Test task update form display"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_update', kwargs={'pk': self.task.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.title)
        self.assertContains(response, self.task.description)
    
    def test_task_update_post_success(self):
        """Test successful task update via POST"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_update', kwargs={'pk': self.task.pk})
        
        updated_data = {
            'title': 'Updated Task Title',
            'description': 'Updated description',
            'priority': 'high',
            'status': 'in_progress',
            'office': self.office.id,
            'assigned_to': self.user.id
        }
        
        response = self.client.post(url, updated_data)
        
        # Should redirect after successful update
        self.assertEqual(response.status_code, 302)
        expected_url = reverse('tasks:task_detail', kwargs={'pk': self.task.pk})
        self.assertRedirects(response, expected_url)
        
        # Check task was updated
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, 'Updated Task Title')
        self.assertEqual(self.task.description, 'Updated description')
        self.assertEqual(self.task.priority, 'high')
        self.assertEqual(self.task.status, 'in_progress')
    
    def test_task_update_completion(self):
        """Test marking task as completed through update"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_update', kwargs={'pk': self.task.pk})
        
        # Mark task as completed
        updated_data = {
            'title': self.task.title,
            'description': self.task.description,
            'priority': self.task.priority,
            'status': 'completed',
            'office': self.office.id,
            'assigned_to': self.user.id
        }
        
        response = self.client.post(url, updated_data)
        
        # Check task completion was handled
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'completed')
        self.assertIsNotNone(self.task.completed_at)
    
    def test_task_update_uncomplete(self):
        """Test unmarking task completion through update"""
        # First mark task as completed
        self.task.status = 'completed'
        self.task.completed_at = timezone.now()
        self.task.completion_notes = 'Task completed'
        self.task.save()
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_update', kwargs={'pk': self.task.pk})
        
        # Mark task as pending again
        updated_data = {
            'title': self.task.title,
            'description': self.task.description,
            'priority': self.task.priority,
            'status': 'pending',
            'office': self.office.id,
            'assigned_to': self.user.id
        }
        
        response = self.client.post(url, updated_data)
        
        # Check task completion was cleared
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'pending')
        self.assertIsNone(self.task.completed_at)
        self.assertEqual(self.task.completion_notes, '')


class TaskDeleteViewTest(TestCase):
    """Test cases for task deletion view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        self.task = Task.objects.create(
            title='Test Task',
            created_by=self.user,
            office=self.office
        )
    
    def test_task_delete_requires_login(self):
        """Test that task deletion requires authentication"""
        url = reverse('tasks:task_delete', kwargs={'pk': self.task.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_task_delete_get(self):
        """Test task deletion confirmation page"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_delete', kwargs={'pk': self.task.pk})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.task.title)
        self.assertContains(response, 'Delete Task')
    
    def test_task_delete_post(self):
        """Test actual task deletion via POST"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_delete', kwargs={'pk': self.task.pk})
        
        task_id = self.task.pk
        response = self.client.post(url)
        
        # Should redirect after deletion
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('tasks:task_list'))
        
        # Check task was deleted
        self.assertFalse(Task.objects.filter(pk=task_id).exists())
    
    def test_recurring_template_deletion(self):
        """Test deleting recurring template with occurrences"""
        # Create recurring template
        template = Task.objects.create(
            title='Recurring Template',
            is_recurring_template=True,
            created_by=self.user,
            office=self.office
        )
        
        # Create some occurrences
        for i in range(3):
            Task.objects.create(
                title=f'Occurrence {i}',
                parent_task=template,
                created_by=self.user,
                office=self.office
            )
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_delete', kwargs={'pk': template.pk})
        
        # Check context includes occurrence count
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['occurrence_count'], 3)
        
        # Delete template
        response = self.client.post(url)
        
        # Template and all occurrences should be deleted
        self.assertFalse(Task.objects.filter(pk=template.pk).exists())
        self.assertEqual(Task.objects.filter(parent_task=template).count(), 0)


class TaskCompleteViewTest(TestCase):
    """Test cases for task completion AJAX view"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        self.task = Task.objects.create(
            title='Test Task',
            status='pending',
            created_by=self.user,
            office=self.office
        )
    
    def test_task_complete_requires_login(self):
        """Test that task completion requires authentication"""
        url = reverse('tasks:task_complete', kwargs={'pk': self.task.pk})
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_task_complete_requires_post(self):
        """Test that task completion requires POST method"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_complete', kwargs={'pk': self.task.pk})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)  # Method not allowed
    
    def test_task_complete_success(self):
        """Test successful task completion"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_complete', kwargs={'pk': self.task.pk})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 200)
        
        # Check JSON response
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'Completed')
        self.assertIsNotNone(data['completed_at_formatted'])
        
        # Check task was marked as completed
        self.task.refresh_from_db()
        self.assertEqual(self.task.status, 'completed')
        self.assertIsNotNone(self.task.completed_at)
    
    def test_task_complete_already_completed(self):
        """Test completing already completed task"""
        # Mark task as completed first
        self.task.status = 'completed'
        self.task.completed_at = timezone.now()
        self.task.save()
        
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_complete', kwargs={'pk': self.task.pk})
        
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 400)
        
        # Check JSON response
        data = response.json()
        self.assertFalse(data['success'])
        self.assertIn('already completed', data['message'])
    
    def test_task_complete_nonexistent(self):
        """Test completing nonexistent task"""
        self.client.login(username='testuser', password='testpass123')
        url = reverse('tasks:task_complete', kwargs={'pk': 99999})
        
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)


class TaskViewIntegrationTest(TestCase):
    """Integration tests for task views"""
    
    def setUp(self):
        """Set up test data"""
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.office = Office.objects.create(
            name='Test Office',
            code='TEST'
        )
        self.person = Person.objects.create(
            first_name='John',
            last_name='Doe',
            email='john@example.com'
        )
    
    def test_complete_task_workflow(self):
        """Test complete task creation, update, and deletion workflow"""
        self.client.login(username='testuser', password='testpass123')
        
        # 1. Create task
        create_url = reverse('tasks:task_create')
        task_data = {
            'title': 'Workflow Task',
            'description': 'Testing complete workflow',
            'priority': 'medium',
            'status': 'pending',
            'person': self.person.id,
            'office': self.office.id,
            'assigned_to': self.user.id
        }
        
        response = self.client.post(create_url, task_data)
        self.assertEqual(response.status_code, 302)
        
        # Find the created task
        task = Task.objects.filter(title='Workflow Task').first()
        self.assertIsNotNone(task)
        
        # 2. View task detail
        detail_url = reverse('tasks:task_detail', kwargs={'pk': task.pk})
        response = self.client.get(detail_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Workflow Task')
        
        # 3. Update task
        update_url = reverse('tasks:task_update', kwargs={'pk': task.pk})
        updated_data = {
            'title': 'Updated Workflow Task',
            'description': 'Updated description',
            'priority': 'high',
            'status': 'in_progress',
            'person': self.person.id,
            'office': self.office.id,
            'assigned_to': self.user.id
        }
        
        response = self.client.post(update_url, updated_data)
        self.assertEqual(response.status_code, 302)
        
        task.refresh_from_db()
        self.assertEqual(task.title, 'Updated Workflow Task')
        self.assertEqual(task.status, 'in_progress')
        
        # 4. Complete task via AJAX
        complete_url = reverse('tasks:task_complete', kwargs={'pk': task.pk})
        response = self.client.post(complete_url)
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertTrue(data['success'])
        
        # 5. Verify completion in task list
        list_url = reverse('tasks:task_list')
        response = self.client.get(list_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Updated Workflow Task')
        
        # 6. Delete task
        delete_url = reverse('tasks:task_delete', kwargs={'pk': task.pk})
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        
        # Verify task is deleted
        self.assertFalse(Task.objects.filter(pk=task.pk).exists())
    
    def test_recurring_task_workflow(self):
        """Test recurring task creation and management workflow"""
        self.client.login(username='testuser', password='testpass123')
        
        # Create recurring template
        create_url = reverse('tasks:task_create')
        recurring_pattern = {
            'frequency': 'daily',
            'interval': 1
        }
        
        task_data = {
            'title': 'Daily Standup',
            'description': 'Daily team standup meeting',
            'priority': 'medium',
            'status': 'pending',
            'is_recurring_template': True,
            'recurring_pattern': json.dumps(recurring_pattern),
            'recurrence_end_date': (timezone.now().date() + timedelta(days=30)),
            'office': self.office.id,
            'assigned_to': self.user.id
        }
        
        response = self.client.post(create_url, task_data)
        self.assertEqual(response.status_code, 302)
        
        # Find the created template
        template = Task.objects.filter(title='Daily Standup', is_recurring_template=True).first()
        self.assertIsNotNone(template)
        self.assertIsNotNone(template.next_occurrence_date)
        
        # Generate some occurrences
        generated_count = template.generate_next_occurrence()
        self.assertIsNotNone(generated_count)
        
        # Verify occurrence was created
        occurrences = Task.objects.filter(parent_task=template)
        self.assertGreater(occurrences.count(), 0)
        
        # Test deleting template (should cascade to occurrences)
        delete_url = reverse('tasks:task_delete', kwargs={'pk': template.pk})
        response = self.client.get(delete_url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('occurrence_count', response.context)
        
        # Actually delete
        response = self.client.post(delete_url)
        self.assertEqual(response.status_code, 302)
        
        # Verify template and occurrences are deleted
        self.assertFalse(Task.objects.filter(pk=template.pk).exists())
        self.assertEqual(Task.objects.filter(parent_task=template).count(), 0)